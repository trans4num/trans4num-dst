import { type FieldVariable } from "@/models/field-variable";
import { generateNumericColor, type ColorScheme } from "@/lib/colors";
import { apiFetch } from "@/lib/api/client";
type FieldVariableResponse = {
    values: Record<string, string | number>;
};

export async function fetchVariables(type: string, alternativeId: string): Promise<FieldVariable[]> {
    const response = await apiFetch(`/fields/variables/${type.toLowerCase()}?simulation=${alternativeId}`);

    if (!response.ok) {
        throw new Error(`Failed to fetch variables for field type ${type} and variable ${alternativeId}: ${response.statusText}`);
    }

    const data: FieldVariableResponse = await response.json();
    const normalizedData = normalizeAndMapColors(data.values, type);
    return normalizedData;
}

// Function to generate a color for categorical values (string-based)
const generateCategoricalColor = (index: number, total: number): string => {
    const hue = Math.round((index / total) * 360); // Spread colors evenly in HSL
    return `hsl(${hue}, 70%, 50%)`;
};

// Function to normalize and map colors dynamically
const normalizeAndMapColors = (input: Record<string, string | number>, type: string): FieldVariable[] => {
    const values = Object.values(input);
    const isNumeric = typeof values[0] === "number"; // Check if we are dealing with numbers

    if (isNumeric) {
        // Handle numerical values
        const numbers = values as number[];
        const min = Math.min(...numbers);
        const max = Math.max(...numbers);
        const scheme: ColorScheme = type === "nLoad" ? "blueToRed" : "redToGreen";
        return Object.entries(input).map(([fieldId, value]) => ({
            fieldId,
            value: parseFloat((value as number).toFixed(3)),
            color: generateNumericColor(value as number, min, max, scheme),
        }));
    } else {
        // Handle categorical values
        const uniqueValues = Array.from(new Set(values.map(v => (v as string).toLowerCase().trim())));
        uniqueValues.sort(); // Sort unique values alphabetically

        const colorMap = Object.fromEntries(
            uniqueValues.map((val, index) => [val, generateCategoricalColor(index, uniqueValues.length)])
        );

        return Object.entries(input).map(([fieldId, value]) => ({
            fieldId,
            value: (value as string).toLowerCase().trim(),
            color: colorMap[(value as string).toLowerCase().trim()] || "#000000",
        }));
    }
};
