// Allow CSS file imports in TypeScript
declare module '*.css' {
  const content: string
  export default content
}
