import {
  Home,
  Users,
  FileCheck,
  ScanFace,
  UserCircle,
} from "lucide-react";
import { NavLink } from "react-router-dom";

export default function Sidebar() {
  const menuItems = [
    {
      name: "Home",
      path: "/dashboard",
      icon: Home,
    },
    {
      name: "People",
      path: "/people",
      icon: Users,
    },
    {
      name: "Documents",
      path: "/documents",
      icon: FileCheck,
    },
    {
      name: "Verify with AI",
      path: "/verification",
      icon: ScanFace,
    },
    {
      name: "Profile",
      path: "/profile",
      icon: UserCircle,
    },
  ];

  return (
    <nav className="mobile-bottom-nav">
      <div className="mobile-nav-brand">
        <div className="mobile-nav-brand-icon">
          <UserCircle size={18} />
        </div>

        <span>TrustVision</span>
      </div>

      <div className="mobile-nav-items">
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `mobile-nav-item ${isActive ? "active" : ""}`
              }
            >
              <Icon size={21} />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}