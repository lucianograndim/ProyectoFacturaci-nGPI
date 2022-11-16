<template>
<div>
    <v-card-title primary-title>
        CRUD
    </v-card-title>
    <v-row justify="center">
        <v-dialog
        v-model="dialog"
        persistent
        max-width="600px"
        >
        <template v-slot:activator="{ on, attrs }">
            <v-btn
            color="lime"
            dark
            v-bind="attrs"
            v-on="on">
            Agregar
            </v-btn>
        </template>
        <v-card>
            <v-card-title>
                <span class="text-h5">Ingrese los datos</span>
            </v-card-title>
            <v-card-text>
                <v-container>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field
                            label="Nombre"
                            required
                            v-model="nameElement"
                            >
                            <v-textarea>
                            </v-textarea>
                            </v-text-field>
                        </v-col>
                        <v-col cols="12">
                            <v-text-field
                            label="Número"
                            required
                            v-model="numberElement">
                            >
                            <v-textarea></v-textarea>
                            </v-text-field>
                        </v-col>
                    </v-row>
                </v-container>
            </v-card-text>
            <v-card-actions>
            <v-spacer></v-spacer>
                <v-btn
                color="#26c6da"
                text
                @click="dialog = false"
                >
                    Cerrar
                </v-btn>
                <v-btn
                color="#26c6da"
                text
                :disabled= "isLoading"
                @click="aggregateItem()"
                >
                    Guardar
                </v-btn>
            </v-card-actions>
        </v-card>
        </v-dialog>
    </v-row>
    <v-spacer></v-spacer>

    <v-col>
        <v-data-table
            :headers="header"
            :items="rows"
            class="elevation-1">
            <template v-slot:item="row">
                <tr>
                    <td>{{row.item.Nombre}}</td>
                    <td>{{row.item.Número}}</td>
                    <td>
                    <v-icon
                    small
                    class="mr-2"
                    @click="editItem(row.item)"
                    >
                    mdi-pencil
                    </v-icon>
                    </td>
                    <td>
                    <v-icon
                    small
                    @click="deleteItem(row.item)"
                    >
                    mdi-delete
                    </v-icon>
                    </td>
                </tr>
            </template>
        </v-data-table>
    </v-col>
    <v-dialog
        v-model="dialogUpdate"
        max-width="900px"
        persistent
        >
        <v-card>
            <v-card-title primary-title>
                Editar
            </v-card-title>
            <v-col cols="12">
                <v-textarea
                    v-model="edit_number">
                </v-textarea>
            </v-col>   
            <v-card-actions>
                <v-btn
                color="#26c6da"
                text
                @click="dialogUpdate = false"
                >
                    Cerrar
                </v-btn>
                <v-btn
                color="#26c6da"
                text
                :disabled= "isLoading"
                @click="sendEdit()"
                >
                    Guardar
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
    <v-dialog
        v-model="dialogDelete"
        max-width="900px"
        persistent>
        <v-card>
        <v-card-title primary-title>
            ¿Esta seguro de eliminar?
        </v-card-title>
        <v-card-actions class="justify-end">
            <v-btn color="#06B7B2" dark @click="sendDelete()">
                Eliminar
            </v-btn>
            <v-btn color="pink" dark @click="dialogDelete = false">
                Cancelar
            </v-btn>
        </v-card-actions>

        
        
        </v-card>

    </v-dialog>
</div>
</template>
<script lang="ts">
     import {Vue, Component} from 'vue-property-decorator';
     import { IDataTable } from '@/model/main/IDataTable';
     import { IHeaderTable } from '@/model/main/IHeaderTable';
     import { internet } from '@/utils/Internet';
     import Util from '@/utils/Util';
     import { ILabels } from '@/model/labels/ILabels';
     import axios from "axios";


@Component({
    name: 'DataTable'
    })
    export default class DataTable{
        public rows: Array<IDataTable> = [];
        public header: Array<IHeaderTable<IDataTable>> = [];
        public isLoading = false;
        public data: Array<ILabels> = [];
        public dialog = false;
        public nameElement = "";
        public numberElement = "";
        public dialogUpdate = false;
        public dialogDelete = false;
        public edit_number = "";
        public current_item = {'Nombre': '', 'Número': ''}; 
    mounted(): void {
        this.getData();
    }

    private getData() {
        this.isLoading = true;
        let config = {
				method: 'get',
				url: 'http://127.0.0.1:9090/model1',
				headers: { Authorization: 'Basic ' + btoa('usuario2' + ':' + '123')}
			};
            axios(config)
            .then((response) => {
                this.data = response.data as Array<ILabels>;
                const dataTable: Array<IDataTable> = [];
                for (let item of this.data) {
                   // console.log(item);
                    const row: IDataTable = {};
                    row['Nombre'] = item.name;
                    row['Número'] = item.number;
                    row['Editar'] = "";
                    row['Eliminar'] = "";
                    //console.log(JSON.stringify(item.tunning))
                    dataTable.push(row);
                }
                const header: Array<IHeaderTable<
                    IDataTable
                >> = Object.keys(dataTable[0]).map(
                    (
                        key: string
                    ): IHeaderTable<IDataTable> => {
                        let text = key;
                        switch (key) {
                            case 'name':
                                text = "Nombre";
                                break;
                            case 'number':
                                text = "Número";
                                break;
                                }
                            return {
                                text,
                                value: key,
							};
                        }
                    ) as Array<IHeaderTable<IDataTable>>;
                    this.rows = dataTable;
                    this.header = header;
                    })
                .catch(console.log)
                .finally(() => {
                this.isLoading = false;
            });
        }

    public editItem(item:ILabels){
        let number = item.Número; 
        this.edit_number = number;
        this.dialogUpdate = true;
        this.current_item = item;
    }
    public sendEdit() {
        let nombre = this.current_item.Nombre;
        let dt = JSON.stringify({
            'name': nombre, 
            'number': this.edit_number
        })
        let config = {
				method: 'post',
				url: 'http://127.0.0.1:9090/model1',
                data: dt,
				headers: { 
                    Authorization: 'Basic ' + btoa('usuario2' + ':' + '123'),
                    'Content-Type': 'application/json'
                }
			};
            axios(config)
			.then(response => {
				this.getData();
                this.dialogUpdate = false;
			})	
    }

    public deleteItem(item:ILabels){
        this.current_item = item;
        this.dialogDelete = true;
    }

    public sendDelete(){
        let nombre = this.current_item.Nombre;
        console.log("delete");
        let config = {
            method: 'delete',
            url: 'http://127.0.0.1:9090/model1',
            params: {'name': nombre},
            headers: { Authorization: 'Basic ' + btoa('usuario2' + ':' + '123')}
        };
        axios(config)
        .then(response => {
            // sacar el item del front
            this.dialogDelete = false;
            this.getData();
        })
    }

    public aggregateItem(){
        let name = this.nameElement;
        let number = this.numberElement;
        let config = {
            method: 'put',
            url: 'http://127.0.0.1:9090/model1',
            params: {'name': name, 'number': number},
            headers: {  Authorization: 'Basic ' + btoa('usuario2' + ':' + '123')}
        };
        axios(config)
			.then(response => {
                this.dialog = false;
                this.nameElement = "";
                this.numberElement = "";
                this.getData();
			})
    }


    }  
</script>