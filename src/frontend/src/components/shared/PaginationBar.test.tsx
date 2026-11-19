import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PaginationBar from "./PaginationBar";

describe("PaginationBar", () => {
  const defaultProps = {
    page: 1,
    totalPages: 5,
    pageSize: 8,
    totalCount: 40,
    onPageChange: vi.fn(),
  };

  it("returns null when totalPages is 1", () => {
    const { container } = render(
      <PaginationBar {...defaultProps} totalPages={1} totalCount={5} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("shows correct range text", () => {
    render(<PaginationBar {...defaultProps} page={2} />);
    expect(screen.getByText(/9–16 of 40/)).toBeTruthy();
  });

  it("shows range for first page", () => {
    render(<PaginationBar {...defaultProps} />);
    expect(screen.getByText(/1–8 of 40/)).toBeTruthy();
  });

  it("clamps range on last page", () => {
    render(
      <PaginationBar {...defaultProps} page={5} totalCount={38} />
    );
    expect(screen.getByText(/33–38 of 38/)).toBeTruthy();
  });

  it("disables previous button on first page", () => {
    render(<PaginationBar {...defaultProps} page={1} />);
    const buttons = screen.getAllByRole("button");
    const prevButton = buttons[0];
    expect(prevButton).toBeDisabled();
  });

  it("disables next button on last page", () => {
    render(<PaginationBar {...defaultProps} page={5} />);
    const buttons = screen.getAllByRole("button");
    const nextButton = buttons[buttons.length - 1];
    expect(nextButton).toBeDisabled();
  });

  it("calls onPageChange when clicking a page number", () => {
    const onPageChange = vi.fn();
    render(<PaginationBar {...defaultProps} onPageChange={onPageChange} />);
    const page3Button = screen.getByText("3");
    fireEvent.click(page3Button);
    expect(onPageChange).toHaveBeenCalledWith(3);
  });

  it("calls onPageChange with prev page on prev click", () => {
    const onPageChange = vi.fn();
    render(
      <PaginationBar {...defaultProps} page={3} onPageChange={onPageChange} />
    );
    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[0]);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("calls onPageChange with next page on next click", () => {
    const onPageChange = vi.fn();
    render(
      <PaginationBar {...defaultProps} page={3} onPageChange={onPageChange} />
    );
    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[buttons.length - 1]);
    expect(onPageChange).toHaveBeenCalledWith(4);
  });

  it("shows ellipsis when totalPages exceeds 7", () => {
    render(<PaginationBar {...defaultProps} totalPages={10} totalCount={80} />);
    expect(screen.getByText("…")).toBeTruthy();
  });

  it("does not show ellipsis when totalPages is 7 or less", () => {
    render(<PaginationBar {...defaultProps} totalPages={5} />);
    expect(screen.queryByText("…")).toBeNull();
  });
});
