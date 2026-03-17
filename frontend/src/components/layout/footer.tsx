import Link from "next/link";
import { LogoAppIcon } from "@/components/ui/logo";

export function Footer() {
  return (
    <footer className="border-t border-border py-16 px-6 bg-secondary/20">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between gap-12">
          <div className="flex flex-col gap-4">
            <Link href="/" className="flex items-center gap-2.5">
              <LogoAppIcon size={32} />
              <span className="text-lg font-display font-bold text-foreground">
                Apply Surge
              </span>
            </Link>
            <p className="text-sm text-muted-foreground max-w-xs leading-relaxed">
              The autonomous AI agent that handles your entire job search
              pipeline.
            </p>
          </div>

          <div className="flex gap-16">
            <div className="flex flex-col gap-3">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">
                Product
              </span>
              <Link href="/features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Features
              </Link>
              <Link href="/pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Pricing
              </Link>
            </div>
            <div className="flex flex-col gap-3">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">
                Account
              </span>
              <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Sign in
              </Link>
              <Link href="/register" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Get Started
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-16 pt-8 border-t border-border flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} Apply Surge. All rights reserved.
          </p>
          <p className="text-xs text-muted-foreground">
            Built by{' '}
            <a
              href="https://paarthpanthri.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-foreground font-medium hover:text-primary transition-colors"
            >
              Paarth Panthri
            </a>
          </p>
          <div className="flex gap-6">
            <span className="text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
              Privacy
            </span>
            <span className="text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
              Terms
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
