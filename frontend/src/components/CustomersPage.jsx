import React, { useState, useEffect } from 'react';
import { customersAPI } from '../services/api';
import { Search, MapPin, User, Phone } from 'lucide-react';

const CustomersPage = () => {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

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

    const filteredCustomers = customers.filter(c =>
        c.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.phone_number?.includes(searchTerm)
    );

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800">Cartera de Clientes</h2>
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                    <input
                        type="text"
                        placeholder="Buscar por nombre o teléfono..."
                        className="pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 w-64"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Teléfono</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dirección</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Desde</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {filteredCustomers.map((customer) => (
                            <tr key={customer.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="flex-shrink-0 h-10 w-10 bg-primary-100 rounded-full flex items-center justify-center">
                                            <User className="text-primary-600" size={20} />
                                        </div>
                                        <div className="ml-4">
                                            <div className="text-sm font-medium text-gray-900">{customer.full_name}</div>
                                            <div className="text-sm text-gray-500">{customer.dni_rif || 'S/I'}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center text-sm text-gray-500">
                                        <Phone size={16} className="mr-2" />
                                        {customer.phone_number}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center text-sm text-gray-500">
                                        <MapPin size={16} className="mr-2 flex-shrink-0" />
                                        <span className="truncate max-w-xs">{customer.main_address || '-'}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {new Date(customer.created_at).toLocaleDateString()}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {filteredCustomers.length === 0 && !loading && (
                    <div className="text-center py-8 text-gray-500">No se encontraron clientes.</div>
                )}
            </div>
        </div>
    );
};

export default CustomersPage;
