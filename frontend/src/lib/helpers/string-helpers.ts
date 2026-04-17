export function camelCaseToSpaced(str: string): string {
  return str
    // Insert a space before any capital letter that follows a lowercase letter
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    // Capitalize the first letter
    .replace(/^./, (match) => match.toUpperCase())
    // Capitalize letters that follow spaces
    .replace(/\s+./g, (match) => match.toUpperCase())
}

export function camelCaseToTitle(str: string) {
  // NOTE: Separates every word by a space and capitalizes the first letter of each word
  // NOTE: This is done because there is no name sent with the chart data - we deduce it from the key
  return str.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').replace(/^\s/, '').replace(/\b\w/g, char => char.toUpperCase());
}
