<script lang="ts">
	import { IPayload } from '@/model/login/IPayload';
	import { IPermission } from '@/model/login/IPermission';
	import { IToken } from '@/model/login/IToken';
	import { Component, Vue } from 'vue-property-decorator';
	import { namespace } from 'vuex-class';
	const storeLogin = namespace('storeLogin');
	@Component({})
	export default class MixinLogin extends Vue {
		@storeLogin.Action
		public login!: (payload: IPayload) => void;
		@storeLogin.Action
		public refreshToken!: (payload: IToken) => void;
		@storeLogin.Action
		public logout!: () => void;

		@storeLogin.Getter
		getToken!: IToken;
		@storeLogin.Getter
		getPermission!: Array<IPermission>;
	}
</script>
