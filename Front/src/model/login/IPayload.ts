import { IPermission } from './IPermission';
import { IToken } from './IToken';
export interface IPayload {
	permission: Array<IPermission>;
	token: IToken;
}
