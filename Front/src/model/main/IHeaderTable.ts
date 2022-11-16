import { IDataTable } from './IDataTable';

export interface IHeaderTable<T = void> {
	text: string;
	value: keyof IDataTable;
	align?: 'start' | 'center' | 'end';
	sortable?: boolean;
	filterable?: boolean;
	groupable?: boolean;
	divider?: boolean;
	class?: string | string[];
	cellClass?: string | string[];
	width?: string | number;
	filter?: (value: any, search: string, item: T) => boolean;
	sort?: (a: any, b: any) => number;
}
