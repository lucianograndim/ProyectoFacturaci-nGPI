<template>
<v-app-bar color="" app>
	<div class="text-center">
	</div>
	<template >
			<div >
			<v-avatar :size=35>
				<img  src="@/assets/global.png"/>
			</v-avatar>
			<select
			class="mx-2"
			v-model="$i18n.locale"
			@change="updateLanguage($event.target.value)"
			variant="info">mdi-chevron-down
			<option
			hide-details
			v-for="(o, i) in locales_array"
			:key="i"
			:value="o.value"
			:selected="o.value === locale_default"
			> {{ o.caption }}
			</option>
			</select>
			</div>
			<v-spacer></v-spacer>
			<v-list>
				<v-list-item @click="listenLogout">
				<v-list-item-title>
					Cerrar Sesión
				</v-list-item-title>
				</v-list-item>
			</v-list>
		</template>
</v-app-bar>
</template>
<script lang="ts">
	import { Component, Vue, Prop } from 'vue-property-decorator';
	import { LOCALES, Locales } from "@/locales/i18n";
	import MixinLogin from '@/mixing/MixinLogin.vue';
	import defaultLocale from "@/i18n";
	@Component({
		name: 'AppBar',
	})
	
	export default class AppBar extends MixinLogin {
		public locales_array = LOCALES;
		public locale_default = defaultLocale;
		@Prop() readonly keycloak!: string

		public listenLogout() {
            //this.logout();
            //Util.showMessage('Hasta pronto', Icon.INFO);
            this.$router.push({
                name: 'Login',
            });
            //this.keycloak.logout();
        }
		public updateLanguage(lang: Locales) {
			console.log("cambiando idioma a ", lang);
			this.$emit('changeEvent', lang);
		}

	}
</script>
