<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  artifactsIn,
  bandOf,
  loadArtifact,
  pick,
  type Locale,
  type RangeArtifact,
} from "../lib/data";

// A 13x13 viewer over data/gen/ranges/*.json. The frequencies come from the artifact; the only thing
// computed here is which grid cell a class key belongs to -- and that mapping is *checked* against the
// artifact's own cell_combos table, so an orientation misunderstanding throws instead of painting a
// plausible wrong chart.

const props = defineProps<{ locale: Locale }>();

const names = artifactsIn("ranges");
const name = ref(names[0] ?? "");
const chart = ref<RangeArtifact | null>(null);
const error = ref("");
const hover = ref("");

async function open(relative: string): Promise<void> {
  error.value = "";
  hover.value = "";
  try {
    chart.value = await loadArtifact<RangeArtifact>(relative);
    // Fail before rendering, not after: if the key convention below is wrong, cell_combos will not
    // contain the key it produces.
    for (const cell of cells(chart.value)) {
      if (chart.value.cell_combos[cell.key] === undefined) {
        throw new Error(
          `${relative}: derived cell key ${cell.key} is absent from cell_combos; the orientation ` +
            `string and this viewer disagree`,
        );
      }
    }
  } catch (problem) {
    chart.value = null;
    error.value = String(problem);
  }
}

watch(name, (value) => void open(value), { immediate: true });

interface Cell {
  key: string;
  frequency: number;
  combos: number;
}

/**
 * Rows and columns are both the rank axis in descending order (A..2). Diagonal = pair; above the
 * diagonal = suited; below = offsuit -- the `orientation` field of every chart artifact states exactly
 * this string and `src/pokergto/matrix13.py` is the authority that writes it.
 */
function cells(artifact: RangeArtifact): Cell[] {
  if (!artifact.orientation.endsWith("-diagonal-pairs-upper-suited")) {
    throw new Error(`unsupported grid orientation: ${artifact.orientation}`);
  }
  const axis = artifact.rows;
  const out: Cell[] = [];
  for (let i = 0; i < axis.length; i += 1) {
    for (let j = 0; j < axis.length; j += 1) {
      const high = axis[Math.min(i, j)];
      const low = axis[Math.max(i, j)];
      const key =
        i === j ? `${high}${low}` : `${high}${low}${j > i ? "s" : "o"}`;
      out.push({
        key,
        frequency: artifact.weights[key] ?? 0,
        combos: artifact.cell_combos[key] ?? 0,
      });
    }
  }
  return out;
}

const grid = computed(() => (chart.value ? cells(chart.value) : []));

const filled = computed(() => grid.value.filter((cell) => cell.frequency > 0).length);

function onCell(cell: Cell): void {
  const combos = cell.frequency * cell.combos;
  hover.value =
    props.locale === "zh"
      ? `${cell.key} · 频率 ${cell.frequency.toFixed(4)} · 满格 ${cell.combos} 组合 · 此格 ${combos.toFixed(2)} 组合`
      : `${cell.key} · frequency ${cell.frequency.toFixed(4)} · full cell ${cell.combos} combos · here ${combos.toFixed(2)}`;
}
</script>

<template>
  <section class="card">
    <div class="head">
      <select v-model="name" aria-label="artifact">
        <option v-for="option in names" :key="option" :value="option">{{ option }}</option>
      </select>
      <span v-if="chart" class="prov" :class="chart.provenance.kind">
        {{ chart.provenance.kind }}
        <template v-if="!chart.provenance.verified"> · UNVERIFIED / 未核验</template>
      </span>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-else-if="chart">
      <h2>{{ pick(chart.title, props.locale) }}</h2>
      <p class="caption">{{ pick(chart.caption, props.locale) }}</p>

      <div class="wrap" @mouseleave="hover = ''">
        <div class="corner"></div>
        <div v-for="rank in chart.columns" :key="`c${rank}`" class="axis">{{ rank }}</div>
        <template v-for="(rank, index) in chart.rows" :key="`r${rank}`">
          <div class="axis">{{ rank }}</div>
          <div
            v-for="cell in grid.slice(index * 13, index * 13 + 13)"
            :key="cell.key"
            class="cell"
            :class="bandOf(cell.frequency)"
            @mouseenter="onCell(cell)"
          >
            {{ cell.key }}
          </div>
        </template>
      </div>

      <p class="legend">
        {{
          props.locale === "zh"
            ? "图例：空格 · 微量 <1% · 低 1-34% · 中 34-67% · 高 67-90% · 满 >90%；对角线为对子，右上三角同花，左下三角不同花。"
            : "Legend: empty · trace <1% · low 1-34% · mid 34-67% · high 67-90% · full >90%; the diagonal is pairs, the upper triangle suited, the lower offsuit."
        }}
      </p>
      <p class="totals">
        <template v-if="props.locale === 'zh'">
          {{ filled }} 个非空格 · 覆盖 {{ chart.total_combos.toFixed(2) }} 组合 = {{
            chart.range_percentage.toFixed(2)
          }}% · 悬停一格看它的组合数
        </template>
        <template v-else>
          {{ filled }} non-empty cells · {{ chart.total_combos.toFixed(2) }} combos = {{
            chart.range_percentage.toFixed(2)
          }}% of 1,326 · hover a cell for its combo count
        </template>
      </p>
      <p class="hover" aria-live="polite">{{ hover }}</p>
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
  text-transform: lowercase;
}
.prov.reference {
  border-color: #b8860b;
  color: #8a6100;
}
.caption {
  margin: 0 0 14px;
  color: var(--muted);
  font-size: 13px;
}
.wrap {
  display: grid;
  grid-template-columns: 26px repeat(13, minmax(0, 1fr));
  gap: 2px;
  max-width: 720px;
}
.corner {
  background: transparent;
}
.axis {
  color: var(--muted);
  font-size: 11px;
  text-align: center;
  align-self: center;
}
.cell {
  aspect-ratio: 1 / 1;
  border-radius: 3px;
  color: #213047;
  font-size: 10px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
  overflow: hidden;
}
.empty {
  background: #eef1f5;
  color: #aab3bf;
}
.trace {
  background: #dbe7fb;
}
.low {
  background: #b3cef8;
}
.mid {
  background: #7fb0f2;
  color: #10233c;
}
.high {
  background: #4c8ae8;
  color: #ffffff;
}
.full {
  background: #1f6feb;
  color: #ffffff;
}
.legend {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 12.5px;
}
.totals {
  margin: 6px 0 0;
  font-size: 12.5px;
  font-variant-numeric: tabular-nums;
}
.hover {
  min-height: 20px;
  margin: 8px 0 0;
  color: var(--accent);
  font-size: 12.5px;
  font-variant-numeric: tabular-nums;
}
</style>
