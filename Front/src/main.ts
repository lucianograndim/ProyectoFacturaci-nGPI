/* import Vue from 'vue'
import './plugins/axios'
import App from './App.vue'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'
import i18n from './i18n'

Vue.config.productionTip = false

new Vue({
  router,
  store,
  vuetify,
  i18n,
  render: h => h(App)
}).$mount('#app') */


import Vue from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
//import VueI18n from 'vue-i18n';
import i18n from './i18n'
import vuetify from './plugins/vuetify';
import Keycloak, { KeycloakOnLoad } from 'keycloak-js';

/* import { messages, defaultLocale } from "@/i18n";

Vue.use(VueI18n)

export const i18n = new VueI18n({
  messages,
  locale: process.env.VUE_APP_I18N_LOCALE || defaultLocale,
  fallbackLocale: process.env.VUE_APP_I18N_FALLBACK_LOCALE || defaultLocale
}); */


Vue.config.productionTip = false

const initOptions = {
  url: process.env.VUE_APP_KEYCLOAK_URL, 
  realm: process.env.VUE_APP_KEYCLOAK_REALM, 
  clientId: process.env.VUE_APP_KEYCLOAK_CLIENT, 
  onLoad: "login-required" as KeycloakOnLoad
}

const keycloak = new Keycloak(initOptions);

keycloak.init({ onLoad: initOptions.onLoad }).then((auth) => {
  if (!auth) {
    window.location.reload();
  } else {
    //Vue.$log.info("Authenticated");
    console.log("Authenticated");

    new Vue({
      el: '#app',
      router,
      store,
      vuetify,
      i18n,
      render: h => h(App, { props: { keycloak: keycloak } })
    })
  }


//Token Refresh
  setInterval(() => {
    keycloak.updateToken(70).then((refreshed) => {
      if (refreshed) {
        //Vue.$log.info('Token refreshed' + refreshed);
        console.log('Token refreshed' + refreshed);
      } else {
        //Vue.$log.warn('Token not refreshed, valid for '
        console.log('Token not refreshed, valid for '
          + Math.round(keycloak.tokenParsed.exp + keycloak.timeSkew - new Date().getTime() / 1000) + ' seconds');
      }
    }).catch(() => {
      //Vue.$log.error('Failed to refresh token');
      console.log('Failed to refresh token');
    });
  }, 6000)

}).catch(() => {
  //Vue.$log.error("Authenticated Failed");
  console.log("Authenticated Failed");
});