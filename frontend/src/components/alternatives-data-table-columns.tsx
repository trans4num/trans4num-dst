"use client";

import { type ColumnDef } from "@tanstack/react-table";
import { Blend, Map, RotateCcw, Trash2 } from "lucide-react";
import { DialogTitle } from "@radix-ui/react-dialog";
import Link from "next/link";
import { useTranslations } from "next-intl";
import AlternativeComparisonCard from "@/components/alternative-comparison-card";
import { DataTableColumnHeader } from "@/components/data-table-header";
import { GoalStatusBadge } from "@/components/goal-status-badge";
import { GoalTypeBadge } from "@/components/goal-type-badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { type Alternative } from "@/models/alternative";

export type AlternativeDeleteActions = {
  isDeletedTab: boolean;
  onDelete: (id: string) => void;
  onRestore: (id: string) => void;
  onPermanentlyDelete: (id: string) => void;
};

export const AlernativeTableColumns = (
  onRowSelect: ((row: Alternative) => void) | undefined,
  statusQuo: Alternative | null | undefined,
  getRowLink: ((row: Alternative) => string) | undefined,
  deleteActions: AlternativeDeleteActions,
): ColumnDef<Alternative>[] => {
  const t = useTranslations("HomePage.columns");

  return [
    {
      id: "select",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("select")} />,
      cell: ({ row }) => (
        <div className="flex items-center justify-center w-fit mx-2" onClick={(e) => e.stopPropagation()}>
          {row.getCanSelect() ? (
            <Checkbox
              checked={row.getIsSelected()}
              onCheckedChange={(value) => {
                row.toggleSelected(!!value);
                onRowSelect?.(row.original);
              }}
              aria-label="Select row"
            />
          ) : (
            <Checkbox disabled />
          )}
        </div>
      ),
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: "name",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("name")} />,
      cell: ({ row }) => <div className="hover:underline">{row.getValue("name")}</div>,
      enableSorting: false,
      enableHiding: false,
      enableColumnFilter: true,
    },
    {
      accessorKey: "status",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("status")} />,
      cell: ({ row }) => <GoalStatusBadge status={row.original.status} />,
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: "goalType",
      accessorFn: (row) => row.model?.goal.type,
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("goal")} />,
      cell: ({ row }) => <GoalTypeBadge goal={row.original.model?.goal} />,
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: "created",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("created")} />,
      cell: ({ row }) => <div>{new Date(row.getValue("created")).toLocaleString()}</div>,
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: "actions",
      header: ({ column }) => <DataTableColumnHeader column={column} title={t("actions")} />,
      cell: ({ row }) => {
        const isDisabled = !row.getCanSelect() || !statusQuo;

        if(deleteActions.isDeletedTab) {
          return (
          <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" onClick={() => deleteActions.onRestore(row.original.id)}>
                    <RotateCcw />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p>{t("restoreLong")}</p>
                </TooltipContent>
              </Tooltip>

              <AlertDialog>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <AlertDialogTrigger asChild>
                      <Button variant="ghost">
                        <Trash2 />
                      </Button>
                    </AlertDialogTrigger>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p>{t("permanentlyDeleteLong")}</p>
                  </TooltipContent>
                </Tooltip>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{t("permanentlyDeleteConfirmTitle")}</AlertDialogTitle>
                    <AlertDialogDescription>
                      {t("permanentlyDeleteConfirmDescription", { name: row.original.name })}
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>{t("permanentlyDeleteConfirmCancel")}</AlertDialogCancel>
                    <AlertDialogAction
                    onClick={() => deleteActions.onPermanentlyDelete(row.original.id)}
                    >
                      {t("permanentlyDeleteConfirmAction")}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          );
        }

        return (
        <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
          <Dialog>
            <Tooltip>
              <TooltipTrigger asChild>
                <DialogTrigger asChild>
                  <Button variant="ghost" disabled={isDisabled}>
                    <Blend />
                  </Button>
                </DialogTrigger>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>{t("compareLong")}</p>
              </TooltipContent>
            </Tooltip>
            <DialogContent className="w-full max-w-6xl mx-auto p-6 sm:p-8 md:p-10">
              <DialogTitle className="hidden"></DialogTitle>
              <AlternativeComparisonCard statusQuo={statusQuo!} selectedAlternatives={[row.original]} />
            </DialogContent>
          </Dialog>
          <Tooltip>
            <TooltipTrigger asChild>
              {isDisabled ? (
                <Button variant="ghost" disabled>
                  <Map />
                </Button>
              ) : (
                <Button variant="ghost" disabled={isDisabled} asChild>
                  <Link href={getRowLink?.(row.original) || ""}>
                    <Map />
                  </Link>
                </Button>
              )}
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p>{t("mapLong")}</p>
            </TooltipContent>
          </Tooltip>
          <AlertDialog>
            <Tooltip>
              <TooltipTrigger asChild>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost">
                    <Trash2 />
                  </Button>
                </AlertDialogTrigger>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>{t("deleteLong")}</p>
              </TooltipContent>
            </Tooltip>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>{t("deleteConfirmTitle")}</AlertDialogTitle>
                <AlertDialogDescription>
                  {t("deleteConfirmDescription", { name: row.original.name })}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>{t("deleteConfirmCancel")}</AlertDialogCancel>
                <AlertDialogAction onClick={() => deleteActions.onDelete(row.original.id)}>
                  {t("deleteConfirmAction")}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
  );
},
      enableSorting: false,
      enableHiding: false,
    },
  ];
};
