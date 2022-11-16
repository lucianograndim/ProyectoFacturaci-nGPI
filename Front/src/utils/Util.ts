import { Icon } from '@/model/util/Icon';
import Swal from 'sweetalert2';
class Util {
	
	public printInformation(text: string): void {
		if (process.env.NODE_ENV !== 'production') {
			console.info(text);
		}
	}

	public async waitForPromises(
		promises: Array<Promise<Record<string, any>>>
	) {
		return Promise.all(promises);
	}
	public async showMessage(
		message: string,
		icon: Icon,
		title?: string
	) {
		return Swal.fire({
			title: title,
			icon: icon,
			text: message,
			toast: false,
			position: 'center',
			showCancelButton: false,
			showConfirmButton: true,
		});
	}
	public async showConfirmationMessage(
		message: string,
		icon: Icon,
		title?: string
	) {
		return Swal.fire({
			title: title,
			icon: icon,
			text: message,
			toast: false,
			position: 'center',
			showDenyButton: true,
			showConfirmButton: true,
			denyButtonText: 'No',
			confirmButtonText: 'Si, hazlo.',
		});
	}
	public replaceTextWith(
		text: string,
		toReplace: string,
		replace: string
	): string {
		return text.replaceAll(toReplace, replace);
	}
	
}

export default new Util();
