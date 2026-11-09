declare module "next" {
  export type Metadata = { title?: string; description?: string };
  export type NextConfig = Record<string, unknown>;
}

declare module "next/link" {
  import type { AnchorHTMLAttributes, ReactNode } from "react";
  export default function Link(props: AnchorHTMLAttributes<HTMLAnchorElement> & { children?: ReactNode }): JSX.Element;
}

declare module "next/navigation" {
  export function usePathname(): string;
  export function useParams<T extends Record<string, string | string[]>>(): T;
}

declare module "next/types.js" {
  export type ResolvingMetadata = any;
  export type ResolvingViewport = any;
}

declare module "next/dist/lib/metadata/types/metadata-interface.js" {
  export type ResolvingMetadata = any;
  export type ResolvingViewport = any;
}

declare module "next/dist/build/segment-config/app/app-segment-config.js" {
  export type InstantConfigForTypeCheckInternal = any;
  export type Prefetch = any;
  export type EnsureStatic = any;
}
