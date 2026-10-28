import { useMemo } from "react";
import { typeColors } from "../lib/colors";

/** The color of each object, by its type. */
export function useColors(objectTypes: readonly string[], typeOf: Record<string, string>) {
  const key = objectTypes.join();
  // keyed by the types' content, not by their array
  const colorOfType = useMemo(() => typeColors(objectTypes), [key]);
  const colorOf = useMemo(
    () => (object: string) => colorOfType(typeOf[object]),
    [colorOfType, typeOf],
  );
  return { colorOf, colorOfType };
}
