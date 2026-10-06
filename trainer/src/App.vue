<script setup lang="ts">
import { computed, ref } from "vue";
import MdfSizingScale from "./views/MdfSizingScale.vue";
import RangeChart from "./views/RangeChart.vue";
import SolverDeck from "./views/SolverDeck.vue";
import QuizDrill from "./views/QuizDrill.vue";
import { manifestInfo, SUPPORTED_SCHEMA, type Locale } from "./lib/data";

// Tabs, not a router: the trainer is a static bundle published under /trainer/, and three screens do
// not need history management. Adding a fourth should not require infrastructure.

type Screen = "sizing" | "ranges" | "solver" | "quiz";

const locale = ref<Locale>("zh");
const screen = ref<Screen>("sizing");

const info = manifestInfo();
const schemaSkew = info.schemaVersion !== SUPPORTED_SCHEMA;

const copy = computed(() =>
  locale.value === "zh"
    ? {
        title: "pokergto 训练器",
        subtitle: "只读 data/gen 的静态产物：数字不是这里算的，是引擎算的。",
        sizing: "尺度滑尺",
        ranges: "13×13 范围图",
        solver: "求解器观察台",
        quiz: "题库速算",
        schema: "数据契约版本与本构建不匹配",
        engine: "引擎",
        artifacts: "可用产物",
      }
    : {
        title: "pokergto trainer",
        subtitle:
          "Reads the committed data/gen artifacts only: no number here is computed in the browser.",
        sizing: "Sizing scale",
        ranges: "13x13 range chart",
        solver: "Solver deck",
        quiz: "Quick drill",
        schema: "artifact schema does not match this build",
        engine: "engine",
        artifacts: "artifacts",
      },
);
</script>

<template>
  <header class="bar">
    <div>
      <h1>{{ copy.title }}</h1>
      <p class="sub">{{ copy.subtitle }}</p>
    </div>
    <div class="status">
      <span class="pill" :class="{ bad: schemaSkew }">
        schema {{ info.schemaVersion }} · {{ copy.engine }} {{ info.engineVersion }} ·
        {{ info.artifactCount }} {{ copy.artifacts }}
      </span>
      <button class="lang" type="button" @click="locale = locale === 'zh' ? 'en' : 'zh'">
        {{ locale === "zh" ? "EN" : "中文" }}
      </button>
    </div>
  </header>

  <nav class="tabs">
    <button :class="{ on: screen === 'sizing' }" type="button" @click="screen = 'sizing'">
      {{ copy.sizing }}
    </button>
    <button :class="{ on: screen === 'ranges' }" type="button" @click="screen = 'ranges'">
      {{ copy.ranges }}
    </button>
    <button :class="{ on: screen === 'solver' }" type="button" @click="screen = 'solver'">
      {{ copy.solver }}
    </button>
    <button :class="{ on: screen === 'quiz' }" type="button" @click="screen = 'quiz'">
      {{ copy.quiz }}
    </button>
  </nav>

  <main>
    <MdfSizingScale v-if="screen === 'sizing'" :locale="locale" />
    <RangeChart v-else-if="screen === 'ranges'" :locale="locale" />
    <QuizDrill v-else-if="screen === 'quiz'" :locale="locale" />
    <SolverDeck v-else :locale="locale" />
  </main>
</template>

<style>
:root {
  --ink: #12151b;
  --muted: #5c6674;
  --line: #d7dce3;
  --bg: #f6f7f9;
  --card: #ffffff;
  --accent: #1f6feb;
  --bad: #b3261e;
}
* {
  box-sizing: border-box;
}
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font: 15px/1.55 ui-sans-serif, system-ui, "Segoe UI", "Noto Sans SC", sans-serif;
}
.bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 22px 12px;
  border-bottom: 1px solid var(--line);
  background: var(--card);
}
.bar h1 {
  margin: 0;
  font-size: 19px;
}
.sub {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 13px;
}
.status {
  display: flex;
  gap: 8px;
  align-items: center;
}
.pill {
  padding: 3px 9px;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.pill.bad {
  border-color: var(--bad);
  color: var(--bad);
}
.lang {
  padding: 3px 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--card);
  cursor: pointer;
  font-size: 12px;
}
.tabs {
  display: flex;
  gap: 6px;
  padding: 10px 22px;
  border-bottom: 1px solid var(--line);
  background: var(--card);
}
.tabs button {
  padding: 6px 12px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
}
.tabs button.on {
  border-color: var(--accent);
  color: var(--accent);
  background: #eaf2fd;
}
main {
  padding: 18px 22px 40px;
}
.card {
  padding: 16px 18px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--card);
}
.error {
  padding: 14px 16px;
  border: 1px solid var(--bad);
  border-radius: 8px;
  color: var(--bad);
  background: #fdf1f0;
  white-space: pre-wrap;
}
h2 {
  margin: 0 0 6px;
  font-size: 16px;
}
.legend {
  color: var(--muted);
  font-size: 12.5px;
}
table {
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}
th,
td {
  padding: 4px 8px;
  border-bottom: 1px solid var(--line);
  text-align: right;
}
th:first-child,
td:first-child {
  text-align: left;
}
</style>
