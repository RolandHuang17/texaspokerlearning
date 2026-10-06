<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  artifactsIn,
  formatCell,
  loadArtifact,
  pick,
  type Locale,
  type TableArtifact,
} from "../lib/data";

// A generated table, slid through one row at a time. Everything on screen is a cell of
// data/gen/tables/*.json: the widget adds a cursor and nothing else, which is what keeps it honest --
// there is no formula in this file that could disagree with pokergto.

const props = defineProps<{ locale: Locale }>();

const names = artifactsIn("tables");
const name = ref(names[0] ?? "");
const table = ref<TableArtifact | null>(null);
const error = ref("");
const row = ref(0);

async function open(relative: string): Promise<void> {
  error.value = "";
  try {
    table.value = await loadArtifact<TableArtifact>(relative);
    row.value = 0;
  } catch (problem) {
    table.value = null;
    error.value = String(problem);
  }
}

watch(name, (value) => void open(value), { immediate: true });

const max = computed(() => (table.value ? table.value.rows.length - 1 : 0));
const current = computed(() =>
  table.value && table.value.rows.length > 0 ? table.value.rows[row.value] : null,
);
const labelColumn = computed(() => {
  if (!table.value) return null;
  const text = table.value.columns.find((column) => column.key.endsWith("label"));
  return text ?? table.value.columns[0] ?? null;
});

watch(row, (value) => {
  if (value > max.value) row.value = max.value;
});
</script>

<template>
  <section class="card">
    <div class="head">
      <select v-model="name" aria-label="artifact">
        <option v-for="option in names" :key="option" :value="option">{{ option }}</option>
      </select>
      <span v-if="table" class="prov" :class="table.provenance.kind">
        {{ table.provenance.kind }}
        <template v-if="!table.provenance.verified"> · UNVERIFIED / 未核验</template>
      </span>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-else-if="table">
      <h2>{{ pick(table.title, props.locale) }}</h2>
      <p class="caption">{{ pick(table.caption, props.locale) }}</p>

      <div class="slider">
        <input v-model.number="row" type="range" min="0" :max="max" step="1" />
        <span class="pos">{{ row + 1 }} / {{ table.rows.length }}</span>
      </div>

      <table v-if="current">
        <tbody>
          <tr v-if="labelColumn && current[labelColumn.key] !== undefined">
            <th>{{ pick(labelColumn.header, props.locale) }}</th>
            <td class="big">{{ formatCell(current[labelColumn.key], labelColumn, props.locale) }}</td>
          </tr>
          <tr
            v-for="column in table.columns.filter((entry) => entry !== labelColumn)"
            :key="column.key"
          >
            <th>{{ pick(column.header, props.locale) }}</th>
            <td>{{ formatCell(current[column.key], column, props.locale) }}</td>
          </tr>
        </tbody>
      </table>

      <p class="source">
        {{ table.source?.module ?? "" }}
        <template v-if="table.source?.function"> #{{ table.source.function }}</template>
        → {{ table.id }}
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
  max-width: 60%;
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
  margin: 0 0 12px;
  color: var(--muted);
  font-size: 13px;
}
.slider {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}
.slider input {
  flex: 1;
}
.pos {
  min-width: 64px;
  color: var(--muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}
table {
  border-collapse: collapse;
  width: 100%;
  max-width: 520px;
}
th,
td {
  padding: 7px 10px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  font-variant-numeric: tabular-nums;
}
th {
  color: var(--muted);
  font-weight: 500;
  font-size: 13px;
}
td.big {
  color: var(--accent);
  font-weight: 600;
}
.source {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 12px;
}
</style>
