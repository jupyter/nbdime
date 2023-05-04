export function urlRStrip(target: string): string {
  if (target.slice(-1) === '/') {
    return target.slice(0, -1);
  }
  return target;
}
