/// <reference types="vite/client" />
declare module 'react' {
  export type SetStateAction<S> = S | ((previous: S) => S)
  export type Dispatch<A> = (value: A) => void
  export function useState<S = any>(initial?: any): [any, Dispatch<any>]
  export function useEffect(effect: () => void | (() => void), dependencies?: readonly unknown[]): void
  export function useCallback<T extends (...arguments_: any[]) => any>(callback: T, dependencies: readonly unknown[]): T
  export function useMemo<T>(factory: () => T, dependencies: readonly unknown[]): T
  export function useRef<T>(initial: T): { current: T }
  export type ReactNode = any
  export type FormEvent<T = any> = any
}
declare module 'react-dom/client' { export const createRoot: any }
declare module 'react/jsx-runtime' { export const jsx: any; export const jsxs: any; export const Fragment: any }
declare namespace React { type ReactNode = any; type FormEvent<T = any> = any }
declare namespace JSX {
  interface IntrinsicAttributes { key?: any }
  interface IntrinsicElements { [elemName: string]: any }
}
