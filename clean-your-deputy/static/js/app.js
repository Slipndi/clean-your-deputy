import { createApp } from 'vue';
import AppContainer from './components/AppContainer.vue';

const app = createApp({});
app.component('app-container', AppContainer);

app.mount('#app');