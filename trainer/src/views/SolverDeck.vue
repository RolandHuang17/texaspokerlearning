<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import {
  artifactsIn,
  loadArtifact,
  pick,
  type Locale,
  type SolverArtifact,
} from "../lib/data";

// Plays a *recorded* solve. The exploitability curve and the average strategy are the bytes an
// engine run wrote into data/gen/solver; nothing here iterates, updates regrets, or pretends to solve
// in the browser (adr/0002: an unverified in-page solve would be the worst number in the repository).

const props = defineProps<{ locale: Locale }>();

const names = artifactsIn("solver");
const name = ref(names[0] ?? "");
const run = ref<SolverArtifact | null>(null);
const error = ref("");
const step = ref(0);
const playing = ref(false);

async function open(relative: string): Promise<void> {
  error.value = "";
  playing.value = false;
  try {
    run.value = await loadArtifact<SolverArtifact>(relative);
    step.value = run.value.curve.length - 1;
  } catch (problem) {
    run.value = null;
    error.value = String(problem);
  }
}

watch(name, (value) => void open(value), { immediate: true });

const curve = computed(() => run.value?.curve ?? []);
const shown = computed(() => curve.value[step.value] ?? null);

let timer: ReturnType<typeof setInterval> | null = null;

function toggle(): void {
  playing.value = !playing.value;
  if (!playing.value) {
    if (timer !== null) clearInterval(timer);
    timer = null;
    return;
  }
  if (step.value >= curve.value.length - 1) step.value = 0;
  timer = setInterval(() => {
    if (step.value >= curve.value.length - 1) {
      playing.value = false;
      if (timer !== null) clearInterval(timer);
      timer = null;
      return;
    }
    step.value += 1;
  }, 160);
}

onUnmounted(() => {
  if (timer !== null) clearInterval(timer);
});

const width = 520;
const height = 170;

// Logarithmic y axis: exploitability spans orders of magnitude and a linear axis would show the whole
// convergence as a line pressed against zero, which teaches nothing about the shape.
const points = computed(() => {
  if (curve.value.length === 0) return "";
  const values = curve.value.map((point) => Math.max(point.exploitability, 1e-9));
  const max = Math.max(...values);
  const min = Math.min(...values);
  const span = Math.log10(max) - Math.log10(min) || 1;
  return values
    .map((value, index) => {
      const x = (index / (curve.value.length - 1)) * width;
      const y = height - ((Math.log10(value) - Math.log10(min)) / span) * (height - 8) - 4;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
});

const played = computed(() => {
  if (!run.value || curve.value.length === 0) return "";
  const progress = step.value / (curve.value.length - 1);
  return points.value
    .split(" ")
    .slice(0, Math.max(1, step.value + 1))
    .join(" ")
    .concat(` ${(progress * width).toFixed(1)},${height - 4}`);
});

const infosets = computed(() =>
  run.value ? Object.keys(run.value.average_strategy).sort() : [],
);
const infoset = ref("");
watch(infosets, (keys) => {
  if (!infoset.value && keys.length > 0) infoset.value = keys[0];
});
</script>

<template>
  <section class="card">
    <div class="head">
      <select v-model="name" aria-label="artifact">
        <option v-for="option in names" :key="option" :value="option">{{ option }}</option>
      </select>
      <span v-if="run" class="prov" :class="{ bad: !run.checks.every((c) => c.pass) }">
        {{ run.checks.every((c) => c.pass) ? "proof gates pass" : "a proof gate failed" }}
      </span>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-else-if="run">
      <h2>{{ pick(run.game_description, props.locale) }}</h2>
      <p class="meta">
        {{ run.algorithm }} · {{ run.iterations }} {{ props.locale === "zh" ? "次迭代" : "iterations" }}
        <template v-if="run.closed_form_value !== undefined">
          · {{ props.locale === "zh" ? "解析值" : "closed form" }} {{ run.closed_form_value }}
        </template>
      </p>

      <svg :viewBox="`0 0 ${width} ${height}`" class="plot" role="img">
        <polyline :points="points" fill="none" stroke="#c9d3e2" stroke-width="1.5" />
        <polyline :points="played" fill="none" stroke="#1f6feb" stroke-width="2" />
        <line
          v-if="shown"
          :x1="(step / Math.max(1, curve.length - 1)) * width"
          :x2="(step / Math.max(1, curve.length - 1)) * width"
          y1="0"
          :y2="height"
          stroke="#9fb0c7"
          stroke-dasharray="3 3"
        />
      </svg>

      <div class="controls">
        <button type="button" @click="toggle">
          {{ playing ? (props.locale === "zh" ? "暂停" : "pause") : props.locale === "zh" ? "播放收敛" : "play convergence" }}
        </button>
        <input
          v-model.number="step"
          type="range"
          min="0"
          :max="Math.max(0, curve.length - 1)"
          step="1"
          aria-label="iteration"
        />
        <span v-if="shown" class="read">
          {{ shown.iteration }} → ε {{ shown.exploitability.toExponential(2) }}
        </span>
      </div>

      <dl class="numbers">
        <div>
          <dt>{{ props.locale === "zh" ? "最终可剥削度" : "final exploitability" }}</dt>
          <dd>{{ run.exploitability_bb_per_hand.toExponential(3) }} bb/hand</dd>
        </div>
        <div>
          <dt>{{ props.locale === "zh" ? "闸门阈值" : "proof threshold" }}</dt>
          <dd>{{ run.exploitability_threshold.toExponential(1) }}</dd>
        </div>
        <div>
          <dt>{{ props.locale === "zh" ? "博弈值" : "game value" }}</dt>
          <dd>{{ run.game_value_bb_per_hand }} bb/hand</dd>
        </div>
      </dl>

      <h3>{{ props.locale === "zh" ? "证明登记表" : "proof ledger" }}</h3>
      <table>
        <tbody>
          <tr v-for="check in run.checks" :key="check.kind">
            <td :class="check.pass ? 'ok' : 'no'">{{ check.pass ? "✓" : "✗" }}</td>
            <td>{{ check.kind }}</td>
            <td class="num">
              {{ check.value !== undefined ? check.value.toPrecision(6) : "" }}
            </td>
            <td class="detail">{{ check.detail }}</td>
          </tr>
        </tbody>
      </table>

      <h3>{{ props.locale === "zh" ? "平均策略" : "average strategy" }}</h3>
      <select v-model="infoset" class="infoset" aria-label="information set">
        <option v-for="key in infosets" :key="key" :value="key">{{ key }}</option>
      </select>
      <ul class="strategy">
        <li v-for="(frequency, action) in run.average_strategy[infoset] ?? {}" :key="action">
          <span class="action">{{ action }}</span>
          <span class="meter"><span :style="{ width: `${frequency * 100}%` }"></span></span>
          <span class="num">{{ frequency.toFixed(4) }}</span>
        </li>
      </ul>
      <p class="legend">
        {{
          props.locale === "zh"
            ? "策略是求解决策过程的平均，不是某一轮当前的策略；纵轴取对数，因为收敛横跨几个数量级。"
            : "This is the average strategy over the solve, not the current strategy of the last iteration; the vertical axis is logarithmic because convergence spans orders of magnitude."
        }}
      </p>
    </template>
  </section>
</template>

<style scoped>
.head {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}
select {
  max-width: 70%;
  padding: 5px 8px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  font: inherit;
}
.prov {
  padding: 2px 8px;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--muted);
  font-size: 12px;
}
.prov.bad {
  border-color: var(--bad);
  color: var(--bad);
}
.meta {
  margin: 0 0 12px;
  color: var(--muted);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
.plot {
  width: 100%;
  max-width: 720px;
  height: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfcfe;
}
.controls {
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 12px 0;
}
.controls input {
  flex: 1;
}
.controls button {
  padding: 6px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font: inherit;
}
.read {
  min-width: 168px;
  color: var(--muted);
  font-size: 12.5px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}
.numbers {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin: 0 0 16px;
}
.numbers dt {
  color: var(--muted);
  font-size: 12px;
}
.numbers dd {
  margin: 2px 0 0;
  font-size: 15px;
  font-variant-numeric: tabular-nums;
}
h3 {
  margin: 16px 0 8px;
  font-size: 14px;
}
table {
  width: 100%;
  max-width: 720px;
  font-size: 13px;
}
td {
  padding: 5px 8px;
}
.ok {
  color: #1a7f37;
}
.no {
  color: var(--bad);
}
.num {
  font-variant-numeric: tabular-nums;
  text-align: right;
  white-space: nowrap;
}
.detail {
  color: var(--muted);
}
.infoset {
  min-width: 200px;
}
.strategy {
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
  max-width: 520px;
}
.strategy li {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 4px;
}
.action {
  min-width: 64px;
  color: var(--muted);
  font-size: 13px;
}
.meter {
  flex: 1;
  height: 10px;
  border-radius: 3px;
  background: #eef1f5;
  overflow: hidden;
}
.meter > span {
  display: block;
  height: 100%;
  background: var(--accent);
}
.legend {
  margin: 14px 0 0;
  color: var(--muted);
  font-size: 12.5px;
}
</style>
