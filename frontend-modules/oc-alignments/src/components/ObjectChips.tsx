import { Group, Text } from "@mantine/core";

// Objects as small pills: a dot in the color of the object's type, and its id.
export default function ObjectChips({
  objects,
  colorOf,
  justify = "flex-start",
}: {
  objects: readonly string[];
  colorOf: (object: string) => string;
  justify?: "flex-start" | "center";
}) {
  return (
    <Group gap={4} justify={justify}>
      {objects.map((object) => {
        const color = colorOf(object);
        return (
          <Group
            key={object}
            gap={4}
            wrap="nowrap"
            px={6}
            style={{
              borderRadius: 999,
              background: `color-mix(in srgb, ${color} 16%, var(--mantine-color-body))`,
              border: `1px solid color-mix(in srgb, ${color} 55%, transparent)`,
              lineHeight: "18px",
            }}
          >
            <span
              aria-hidden
              style={{ width: 7, height: 7, borderRadius: "50%", background: color, flex: "none" }}
            />
            <Text size="xs" fw={500}>
              {object}
            </Text>
          </Group>
        );
      })}
    </Group>
  );
}
