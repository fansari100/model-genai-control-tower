"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Cpu,
  Wrench,
  Sparkles,
  FlaskConical,
  AlertTriangle,
  FileCheck2,
  Shield,
  Settings,
  ShieldCheck,
  Play,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Models", href: "/models", icon: Cpu },
  { name: "Tools & EUCs", href: "/tools", icon: Wrench },
  { name: "GenAI Use Cases", href: "/use-cases", icon: Sparkles },
  { name: "Evaluations", href: "/evaluations", icon: FlaskConical },
  { name: "Findings", href: "/findings", icon: AlertTriangle },
  { name: "Certifications", href: "/certifications", icon: FileCheck2 },
  { name: "Compliance Matrix", href: "/compliance", icon: ShieldCheck },
  { name: "Live Model Demo", href: "/demo", icon: Play },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="hidden lg:flex lg:flex-shrink-0">
      <div className="flex w-64 flex-col">
        <div className="flex min-h-0 flex-1 flex-col border-r border-gray-200 bg-white">
          {/* Logo */}
          <div className="flex h-16 items-center gap-3 border-b border-gray-200 px-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900">Control Tower</h1>
              <p className="text-xs text-gray-500">Model & GenAI Governance</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const isActive =
                pathname === item.href || pathname?.startsWith(item.href + "/");
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  )}
                >
                  <item.icon
                    className={cn(
                      "h-4 w-4",
                      isActive ? "text-primary" : "text-gray-400"
                    )}
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Compliance Frameworks */}
          <div className="border-t border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 mb-2">
              Active Compliance Frameworks
            </p>
            <div className="flex flex-wrap gap-1">
              {[
                "SR 11-7",
                "NIST 600-1",
                "OWASP LLM",
                "OWASP Agentic",
                "ISO 42001",
                "MITRE ATLAS",
                "FINRA",
              ].map((fw) => (
                <span
                  key={fw}
                  className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-600"
                >
                  {fw}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
