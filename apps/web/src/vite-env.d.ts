/// <reference types="vite/client" />
declare module 'react' {
  export const useState: any
  export const useEffect: any
  export type ReactNode = any
  export type FormEvent<T = any> = any
}
declare module 'react-dom/client' { export const createRoot: any }
declare module 'react/jsx-runtime' { export const jsx: any; export const jsxs: any; export const Fragment: any }
declare namespace JSX { interface IntrinsicElements { [elemName: string]: any } }
