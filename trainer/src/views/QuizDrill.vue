<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { artifactsIn, loadArtifact, pick, type Locale } from "../lib/data";

// A drill over generated quiz items. The number a learner types is compared against `answer.number`,
// which tools/gen_quizzes.py obtained from pokergto and tools/check_quiz_answers.py re-derives in CI --
// so the app is checking against arithmetic, not against a key somebody wrote into a file.

const props = defineProps<{ locale: Locale }>();

interface QuizItem {
  id: string;
  lesson?: string | null;
  prompt: { zh: string; en: string };
  answer: { number?: number | null };
  tolerance?: { absolute?: number | null };
  rationale: { zh: string; en: string };
  derivationRef?: string;
}

const ids = artifactsIn("quizzes");
const index = ref(0);
const item = ref<QuizItem | null>(null);
const error = ref("");
const entry = ref("");
const verdict = ref<"" | "correct" | "wrong">("");
const seen = ref(0);
const correct = ref(0);

async function open(position: number): Promise<void> {
  error.value = "";
  verdict.value = "";
  entry.value = "";
  const relative = ids[position];
  if (!relative) return;
  try {
    const raw = await loadArtifact<Record<string, unknown>>(relative);
    item.value = {
      id: String(raw.id),
      lesson: (raw.lesson as string) ?? null,
      prompt: raw.prompt as { zh: string; en: string },
      answer: raw.answer as { number?: number | null },
      tolerance: raw.tolerance as { absolute?: number | null } | undefined,
      rationale: raw.rationale as { zh: string; en: string },
      derivationRef: (raw.derivation_ref as string) ?? undefined,
    };
  } catch (problem) {
    item.value = null;
    error.value = String(problem);
  }
}

watch(index, (position) => void open(position));
onMounted(() => void open(0));

const expected = computed(() => item.value?.answer?.number ?? null);

function grade(): void {
  const current = item.value;
  const want = expected.value;
  const given = Number(entry.value.replace(",", "."));
  if (!current || want === null || Number.isNaN(given)) {
    verdict.value = "wrong";
    return;
  }
  const tolerance = current.tolerance?.absolute ?? 5e-5;
  const hit = Math.abs(given - want) <= Math.max(tolerance, Math.abs(want) * 1e-4);
  verdict.value = hit ? "correct" : "wrong";
  seen.value += 1;
  correct.value += hit ? 1 : 0;
}

function next(): void {
  index.value = (index.value + 1) % ids.length;
}

const asPercent = computed(() => {
  const kind = (item.value?.derivationRef ?? "").includes("value_to_bluff") ? false : true;
  return kind && expected.value !== null ? (expected.value * 100).toFixed(2) + "%" : null;
});
</script>

<template>
  <section class="card">
    <div class="head">
      <span class="counter">{{ ids.length ? index + 1 : 0 }} / {{ ids.length }}</span>
      <span v-if="ids.length" class="score">
        {{ props.locale === "zh" ? "已答" : "answered" }} {{ seen }} ·
        {{ props.locale === "zh" ? "对" : "correct" }} {{ correct }}
      </span>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="!ids.length" class="legend">
      {{
        props.locale === "zh"
          ? "题库还没有产物：先跑 python tools/gen_all.py --only quizzes。"
          : "No quiz artifacts yet: run python tools/gen_all.py --only quizzes."
      }}
    </p>

    <template v-else-if="item">
      <p class="prompt">{{ pick(item.prompt, props.locale) }}</p>
      <form class="row" @submit.prevent="grade">
        <input v-model="entry" inputmode="decimal" :placeholder="props.locale === 'zh' ? '你的答案' : 'your answer'" />
        <button type="submit">{{ props.locale === "zh" ? "判分" : "grade" }}</button>
        <button v-if="verdict" type="button" @click="next">
          {{ props.locale === "zh" ? "下一题" : "next" }}
        </button>
      </form>

      <p v-if="verdict" :class="['verdict', verdict]">
        <template v-if="verdict === 'correct'">
          {{ props.locale === "zh" ? "对。" : "Correct." }}
        </template>
        <template v-else>
          {{
            props.locale === "zh"
              ? "不对。引擎给的答案是："
              : "Not right. The engine's answer is:"
          }}
          <b>{{ expected }}</b>
          <template v-if="asPercent"> ({{ asPercent }})</template>
        </template>
      </p>
      <p v-if="verdict" class="rationale">{{ pick(item.rationale, props.locale) }}</p>
      <p class="source">{{ item.derivationRef }} → {{ item.id }}</p>
    </template>
  </section>
</template>

<style scoped>
.head {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
  color: var(--muted);
  font-size: 12.5px;
  font-variant-numeric: tabular-nums;
}
.prompt {
  margin: 0 0 12px;
  font-size: 16px;
  line-height: 1.6;
}
.row {
  display: flex;
  gap: 8px;
}
input {
  width: 190px;
  padding: 7px 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  font: inherit;
}
button {
  padding: 7px 13px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font: inherit;
}
.verdict {
  margin: 12px 0 0;
  font-weight: 600;
}
.verdict.correct {
  color: #1a7f37;
}
.verdict.wrong {
  color: var(--bad);
}
.rationale {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 13px;
}
.source {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 11.5px;
}
</style>
