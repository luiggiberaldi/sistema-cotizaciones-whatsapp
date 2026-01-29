import React, { useState, useEffect } from 'react';
import { customersAPI } from '../services/api';
import { Search, MapPin, User, Phone, Trash2 } from 'lucide-react';
import ConfirmationModal from './ConfirmationModal';
import AlertModal from './AlertModal';

const CustomersPage = () => {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    // UI State
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [customerToDelete, setCustomerToDelete] = useState(null);
    const [alertModal, setAlertModal] = useState({ isOpen: false, title: '', message: '', type: 'error' });

    useEffect(() => {
        loadCustomers();
    }, []);

    const loadCustomers = async () => {
        try {
            setLoading(true);
            const data = await customersAPI.getAll();
            setCustomers(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    // Open confirmation modal
    const onClickDelete = (customer) => {
        setCustomerToDelete(customer);
        setDeleteModalOpen(true);
    };

    // Actual delete logic
    const confirmDelete = async () => {
        if (!customerToDelete) return;

        try {
            await customersAPI.delete(customerToDelete.id);
            setCustomers(customers.filter(c => c.id !== customerToDelete.id));
            setDeleteModalOpen(false);
            setCustomerToDelete(null);
        } catch (error) {
            console.error(error);
            setDeleteModalOpen(false); // Close confirm modal to show error

            if (error.response?.status === 400) {
                setAlertModal({
                    isOpen: true,
                    title: 'No se puede eliminar',
                    message: error.response.data.detail || "No se puede eliminar porque tiene cotizaciones asociadas.",
                    type: 'error'
                });
            } else {
                setAlertModal({
                    isOpen: true,
                    title: 'Error',
                    message: "Ocurrió un error inesperado al eliminar el cliente.",
                    type: 'error'
                });
            }
        }
    };

    const filteredCustomers = customers.filter(c =>
        c.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.phone_number?.includes(searchTerm)
    );

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <h2 className="text-2xl font-bold text-gray-800">Cartera de Clientes</h2>
                <div className="relative w-full sm:w-64">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                    <input
                        type="text"
                        placeholder="Buscar por nombre o teléfono..."
                        className="pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {/* Vista Mobile: Cards */}
            <div className="grid grid-cols-1 gap-4 sm:hidden">
                {filteredCustomers.map((customer) => (
                    <div key={customer.id} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col gap-3 relative">
                        <button
                            onClick={() => onClickDelete(customer)}
                            className="absolute top-2 right-2 text-gray-400 hover:text-red-600 p-2 transition-colors"
                        >
                            <Trash2 size={18} />
                        </button>

                        <div className="flex items-center gap-3">
                            <div className="h-12 w-12 bg-primary-100 rounded-full flex items-center justify-center shrink-0">
                                <User className="text-primary-600" size={24} />
                            </div>
                            <div className="min-w-0 flex-1">
                                <p className="font-bold text-gray-900 truncate text-lg leading-tight">
                                    {customer.full_name}
                                </p>
                                <p className="text-sm text-gray-500 font-medium">
                                    ID: {customer.dni_rif || 'S/I'}
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 gap-2 border-t pt-3">
                            <div className="flex items-center text-sm text-gray-600 font-medium">
                                <div className="bg-gray-100 p-1.5 rounded-lg mr-2">
                                    <Phone size={14} className="text-gray-500" />
                                </div>
                                {customer.phone_number}
                            </div>
                            <div className="flex items-start text-sm text-gray-600">
                                <div className="bg-gray-100 p-1.5 rounded-lg mr-2 shrink-0">
                                    <MapPin size={14} className="text-gray-500" />
                                </div>
                                <span className="leading-relaxed">
                                    {customer.main_address || 'Sin dirección registrada'}
                                </span>
                            </div>
                        </div>

                        <div className="text-[10px] text-gray-400 font-medium uppercase tracking-wider mt-1 pt-2 border-t border-dashed">
                            Cliente desde: {new Date(customer.created_at).toLocaleDateString()}
                        </div>
                    </div>
                ))}
            </div>

            {/* Vista Desktop: Table */}
            <div className="hidden sm:block bg-white shadow rounded-lg overflow-hidden border border-gray-100">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Teléfono</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dirección</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Desde</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {filteredCustomers.map((customer) => (
                            <tr key={customer.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="flex-shrink-0 h-10 w-10 bg-primary-100 rounded-full flex items-center justify-center">
                                            <User className="text-primary-600" size={20} />
                                        </div>
                                        <div className="ml-4">
                                            <div className="text-sm font-bold text-gray-900">{customer.full_name}</div>
                                            <div className="text-xs text-gray-500">{customer.dni_rif || 'S/I'}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center text-sm text-gray-700 font-medium">
                                        <Phone size={16} className="mr-2 text-gray-400" />
                                        {customer.phone_number}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center text-sm text-gray-600">
                                        <MapPin size={16} className="mr-2 flex-shrink-0 text-gray-400" />
                                        <span className="truncate max-w-xs">{customer.main_address || '-'}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-medium">
                                    {new Date(customer.created_at).toLocaleDateString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button
                                        onClick={() => onClickDelete(customer)}
                                        className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded-full transition-colors"
                                        title="Eliminar Cliente"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {filteredCustomers.length === 0 && !loading && (
                <div className="text-center py-12 bg-white rounded-xl border-2 border-dashed border-gray-100">
                    <User size={48} className="mx-auto text-gray-200 mb-3" />
                    <p className="text-gray-500 text-lg font-medium">No se encontraron clientes.</p>
                </div>
            )}

            <ConfirmationModal
                isOpen={deleteModalOpen}
                onClose={() => setDeleteModalOpen(false)}
                onConfirm={confirmDelete}
                title="Eliminar Cliente"
                message={`¿Estás seguro de que deseas eliminar a ${customerToDelete?.full_name}? Esta acción no se puede deshacer.`}
                isDanger={true}
            />

            <AlertModal
                isOpen={alertModal.isOpen}
                onClose={() => setAlertModal({ ...alertModal, isOpen: false })}
                title={alertModal.title}
                message={alertModal.message}
                type={alertModal.type}
            />
        </div>
    );
};

export default CustomersPage;
