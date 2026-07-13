import { Bell, Menu } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function TopNav() {
  return (
    <header className="h-14 border-b bg-background flex items-center justify-between px-4">
      <div className="flex items-center space-x-4">
        <Menu className="w-5 h-5 md:hidden" />
        <span className="font-semibold text-sm hidden md:inline-block">Dashboard</span>
      </div>
      
      <div className="flex items-center space-x-4">
        <button className="relative">
          <Bell className="w-5 h-5 text-muted-foreground" />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        <Avatar className="w-8 h-8">
          <AvatarImage src="" />
          <AvatarFallback>AD</AvatarFallback>
        </Avatar>
      </div>
    </header>
  );
}
