import { useCurrentOcel } from "@ocelescope/core";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";
import { Alert, Center, Group, Loader, Stack, Text, Title } from "../components";
import AlignmentDetail from "../features/alignment/AlignmentDetail";
import ResultPicker from "../features/results/ResultPicker";
import Summary from "../features/results/Summary";
import { useResult, useResults } from "../features/results/useResults";
import VariantList from "../features/results/VariantList";
import RunBar from "../features/run/RunBar";
import { useColors } from "../hooks/useColors";

// Object-centric alignments of the log selected in Ocelescope: align it with a Petri net, then
// explore the result: its summary, its variants, and the alignment of one of them.
export default function ObjectCentricAlignmentsPage() {
  const { id: ocelId } = useCurrentOcel();
  if (!ocelId) return null; // the route requires a log
  // a new log starts afresh
  return <Alignments key={ocelId} ocelId={ocelId} />;
}

function Alignments({ ocelId }: { ocelId: string }) {
  const results = useResults(ocelId).data;
  const requested = useRouter().query.alignments;
  const [resultId, setResultId] = useState<string | null>(null);
  const [variantId, setVariantId] = useState<string | null>(null);
  const result = useResult(resultId);

  const open = useCallback((alignmentsId: string) => {
    setResultId(alignmentsId);
    setVariantId(null);
  }, []);

  // show the requested result, else the newest
  useEffect(() => {
    if (!results || results.some((r) => r.id === resultId)) return;
    const pick = results.find((r) => r.id === requested) ?? results[0];
    setResultId(pick?.id ?? null);
  }, [results, resultId, requested]);

  // open the most frequent deviating variant, else the most frequent one
  const variants = result.data?.variants;
  useEffect(() => {
    if (!variants || variantId) return;
    const pick = variants.find((v) => (v.deviations ?? 0) > 0) ?? variants[0];
    if (pick) setVariantId(pick.id);
  }, [variants, variantId]);

  const { colorOfType } = useColors(result.data?.objectTypes ?? [], {});

  return (
    <Stack p="md" gap="md">
      <Group justify="space-between" align="center">
        <Title order={2}>Object-Centric Alignments</Title>
        {results && <ResultPicker results={results} selected={resultId} onSelect={open} />}
      </Group>
      <RunBar ocelId={ocelId} onAligned={open} />
      {result.isError ? (
        <Alert color="red" title="The result could not be read" />
      ) : result.data ? (
        <>
          <Summary summary={result.data.summary} />
          <VariantList
            variants={result.data.variants}
            selected={variantId}
            onSelect={setVariantId}
            colorOfType={colorOfType}
          />
          {resultId && variantId && (
            <AlignmentDetail
              key={`${resultId}-${variantId}`}
              alignmentsId={resultId}
              variantId={variantId}
              objectTypes={result.data.objectTypes}
            />
          )}
        </>
      ) : resultId ? (
        <Center h={160}>
          <Loader size="sm" />
        </Center>
      ) : (
        results && (
          <Text c="dimmed" ta="center" mt="xl">
            Pick an object-centric Petri net and press Align to align this log with it.
          </Text>
        )
      )}
    </Stack>
  );
}
