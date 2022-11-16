import { ScopeType } from './ScopeType';

export interface IPermission {
	rsid: string;
	rsname: string;
	scopes: Array<ScopeType>;
}
