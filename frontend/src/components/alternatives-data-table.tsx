"use client";

import {
  type ColumnDef,
  type ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Search, X } from "lucide-react";
import { useTranslations } from "next-intl";

import { type Alternative } from "@/models/alternative";
import { AlternativeConfigurationDialog } from "@/components/alternative-configuration-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface DataTableProps {
  columns: ColumnDef<Alternative>[];
  data: Alternative[];
  onRowSelect?: (row: Alternative) => void;
  getRowLink?: (row: Alternative) => string;
  selectedRow?: Alternative | null;
}

export function PreventRowClickWrapper({ children }: { children: React.ReactNode }) {
  return <div onClick={(e) => e.stopPropagation()}>{children}</div>;
}

export function AlternativesDataTable({
  columns,
  data,
  onRowSelect: _onRowSelect,
  getRowLink,
  selectedRow,
}: DataTableProps) {
  const t = useTranslations("AlternativeTable");
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({});
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [clickedAlternative, setClickedAlternative] = useState<Alternative | null>(null);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onRowSelectionChange: setRowSelection,
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getFilteredRowModel: getFilteredRowModel(),
    state: { rowSelection, sorting, columnFilters, globalFilter },
    enableColumnFilters: true,
    enableRowSelection: (row) =>
      (row.original as Alternative).status !== "processing" &&
      (row.original as Alternative).status !== "failed",
    globalFilterFn: (row, _columnId, filterValue) => {
      const searchValue = filterValue.toLowerCase();
      const name = row.original.name;
      const goalName = row.original.model?.goal?.name;
      const goalType = row.original.model?.goal?.type;

      return !!(
        name.toLowerCase().includes(searchValue) ||
        (goalName && goalName.toLowerCase().includes(searchValue)) ||
        (goalType && goalType.toLowerCase().includes(searchValue))
      );
    },
  });
  const router = useRouter();

  const currentPageIndex = table.getState().pagination.pageIndex;
  const pageSize = table.getState().pagination.pageSize;
  const totalRows = table.getRowCount();
  const startRow = currentPageIndex * pageSize + 1;
  const endRow = Math.min(currentPageIndex * pageSize + pageSize, totalRows);

  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="flex items-center justify-between space-x-2">
        <div className="flex items-center w-[25%]">
          <div className="flex items-center border border-input rounded-md px-3 w-full">
            {globalFilter === "" ? (
              <Search className="h-4 w-4 shrink-0 opacity-50" />
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setGlobalFilter("")}
                className="h-auto p-0 hover:bg-transparent"
                aria-label="Clear Search"
              >
                <X className="h-4 w-4 shrink-0 opacity-50" />
              </Button>
            )}
            <Input
              placeholder={t("search")}
              value={globalFilter ?? ""}
              onChange={(event) => setGlobalFilter(event.target.value)}
              className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 shadow-none"
            />
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <div className="flex justify-center items-center space-x-2 text-sm min-w-24">
            <p>{t("showing", { start: startRow, end: endRow, total: totalRows })}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
      <div className="rounded-md border relative w-full flex flex-col">
        <div className="w-full flex flex-col h-fit">
          <Table>
            <TableHeader className="sticky top-0 bg-background z-10">
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id} style={{ width: header.getSize() }}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
          </Table>
          <div className="flex-1 min-h-0 overflow-auto">
            <Table>
              <TableBody>
                {table.getRowModel().rows?.length ? (
                  table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
                      data-state={row.original === selectedRow ? "selected" : undefined}
                      className="cursor-pointer hover:bg-muted/50 data-[state=selected]:bg-muted"
                      onClick={() => {
                          setClickedAlternative(row.original as Alternative);
                      }}
                    >
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id} style={{ width: cell.column.getSize() }}>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center">
                      No results.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
      {clickedAlternative ? (
        <AlternativeConfigurationDialog
          alternative={clickedAlternative}
          setAlternative={setClickedAlternative}
        />
      ) : null}
    </div>
  );
}
