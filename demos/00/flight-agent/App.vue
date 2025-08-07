<script setup lang="ts">
import AIAgent from "./AIAgent.vue";
</script>

<template>
  <v-container class="ai-agent-container" fluid>
    <div class="ai-agent-wrapper">
      <AIAgent />
    </div>
  </v-container>
</template>

<style>
@import "./styles.css";
@import "./icons.min.css";

.ai-agent-container {
  height: 100vh;
  padding: 16px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.ai-agent-wrapper {
  width: 100%;
  max-width: 800px;
  height: calc(100vh - 32px);
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .ai-agent-container {
    padding: 8px;
  }
  
  .ai-agent-wrapper {
    height: calc(100vh - 16px);
    border-radius: 8px;
  }
}

@media (max-width: 480px) {
  .ai-agent-container {
    padding: 4px;
  }
  
  .ai-agent-wrapper {
    height: calc(100vh - 8px);
    border-radius: 4px;
  }
}
</style>
