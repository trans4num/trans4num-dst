import { AuthGuard } from "@/components/auth-guard";
import { AppSidebar } from "@/components/app-sidebar";
import { Header } from "@/components/header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthGuard requireAuth={true}>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="h-screen">
          <Header />
          <div className="flex-1 flex flex-col gap-4 p-4 pb-0 pt-0 min-h-0">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </AuthGuard>
  );
}
