import { Group, ObjectChips, ScrollArea, Stack, Text, TraceAlignmentStrip } from "../../components";
import { toStripMove } from "../../lib/strip";
import type { ResolvedMove } from "./moves";

// Each object's path through the alignment: the moves that involve it, in order, as a two-row
// strip (log above, model below, ≫ where a side skips). Where the graph shows how objects meet,
// these show what happened to each of them.
export default function ObjectStrips({
  moves,
  objects,
  colorOf,
}: {
  moves: readonly ResolvedMove[];
  objects: readonly string[];
  colorOf: (object: string) => string;
}) {
  return (
    <ScrollArea type="auto" scrollbars="x">
      <Stack gap="sm" py={4}>
        {objects.map((object) => {
          const own = moves.filter((move) => move.objects.includes(object)).map(toStripMove);
          return (
            <Group key={object} gap="sm" wrap="nowrap">
              <Group w={120} justify="flex-end" style={{ flex: "none" }}>
                <ObjectChips objects={[object]} colorOf={colorOf} />
              </Group>
              {own.length > 0 ? (
                <TraceAlignmentStrip moves={own} singleLine />
              ) : (
                <Text size="xs" c="dimmed">
                  –
                </Text>
              )}
            </Group>
          );
        })}
      </Stack>
    </ScrollArea>
  );
}
