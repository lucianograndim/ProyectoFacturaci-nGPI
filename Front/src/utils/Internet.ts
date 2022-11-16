import Axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

class Internet {
	private axios: AxiosInstance;
	constructor() {
		this.axios = Axios.create({
			baseURL: process.env.VUE_APP_API,
			headers: {
				'Content-Type': 'application/json',
			},
		});

		this.axios.interceptors.request.use(
			(config: AxiosRequestConfig) => {
				if (localStorage.getItem('TOKEN') !== null) {
					config.headers!.Authorization = `Bearer ${localStorage.getItem(
						'TOKEN'
					)}`;
				}
				return config;
			}
		);
	}

	public newRequest(): AxiosInstance {
		return this.axios;
	}
}

export const internet = new Internet();
