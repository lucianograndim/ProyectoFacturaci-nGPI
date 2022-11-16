export interface INavigator {
	title: string;
	urlName?: string;
	parent: string;
	module?: string;
	subMenus?: string | number | object;
	selected?: number;
}
