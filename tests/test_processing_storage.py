import io
import json
from unittest.mock import Mock

import pytest

from src.processing.main import main


def setup_client(monkeypatch, tmp_path, extra=()):
    client = Mock()
    client.get_object.return_value = {"Body": io.BytesIO(b"[]")}
    monkeypatch.setattr("boto3.client", lambda *a, **kw: client)
    for name in ("SEAWEEDFS_ENDPOINT_URL", "SEAWEEDFS_ACCESS_KEY", "SEAWEEDFS_SECRET_KEY"):
        monkeypatch.setenv(name, "test")
    monkeypatch.setenv("SEAWEEDFS_RAW_BUCKET", "news-raw")
    monkeypatch.setenv("SEAWEEDFS_PROCESSED_BUCKET", "news-processed")
    monkeypatch.setattr("sys.argv", ["processing", "--output-dir", str(tmp_path), *extra])
    return client


def test_running_processing_uploads_json_without_flag(monkeypatch, tmp_path):
    client = setup_client(monkeypatch, tmp_path)
    main()
    assert client.put_object.call_count == 3
    assert {call.kwargs["Key"] for call in client.put_object.call_args_list} == {
        "aljazeera/silver/processed_articles.json", "aljazeera/silver/rejected.json",
        "aljazeera/silver/report.json",
    }
    for call in client.put_object.call_args_list:
        values = call.kwargs
        assert values["Bucket"] == "news-processed"
        assert values["Key"].endswith(".json")
        assert json.loads(values["Body"]) == json.loads((tmp_path / values["Key"].split("/")[-1]).read_text(encoding="utf-8"))


def test_local_preview_does_not_upload(monkeypatch, tmp_path):
    source = tmp_path / "input.json"
    source.write_text("[]", encoding="utf-8")
    client = setup_client(monkeypatch, tmp_path, ["--input", str(source), "--local-only"])
    main()
    client.put_object.assert_not_called()
    client.get_object.assert_not_called()


def test_upload_failure_is_not_reported_as_success(monkeypatch, tmp_path):
    client = setup_client(monkeypatch, tmp_path)
    client.put_object.side_effect = RuntimeError("upload failed")
    with pytest.raises(RuntimeError, match="upload failed"):
        main()
