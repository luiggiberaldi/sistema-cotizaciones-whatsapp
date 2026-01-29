import React, { useState, useEffect } from 'react';
import { Save, Store, Truck, CreditCard } from 'lucide-react';
import { businessInfoAPI } from '../services/api';

const BusinessInfoPage = () => {
    const [info, setInfo] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState('');

    useEffect(() => {
        loadInfo();
    }, []);

    const loadInfo = async () => {
        try {
            const data = await businessInfoAPI.getBusinessInfo();
            // Convertir array a objeto key-value
            const infoMap = {};
            data.forEach(item => {
                infoMap[item.key] = item.value;
            });
            setInfo(infoMap);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setError('Error cargando información del negocio');
            setLoading(false);
        }
    };

    const handleChange = (key, value) => {
        setInfo(prev => ({
            ...prev,
            [key]: value
        }));
    };

    const handleSave = async () => {
        setSaving(true);
        setError(null);
        setSuccessMessage('');

        try {
            // Convertir objeto key-value a array de updates
            const updates = Object.keys(info).map(key => ({
                key: key,
                value: info[key]
            }));

            await businessInfoAPI.updateBusinessInfo(updates);
            setSuccessMessage('¡Información actualizada con éxito! ✅');

            // Limpiar mensaje después de 3s
            setTimeout(() => setSuccessMessage(''), 3000);
        } catch (err) {
            console.error(err);
            setError('Error guardando cambios');
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="text-center p-8">Cargando configuración...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                    <Store className="text-primary-600" />
                    Configuración del Negocio
                </h2>
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                    <Save size={20} />
                    {saving ? 'Guardando...' : 'Guardar Cambios'}
                </button>
            </div>

            {error && (
                <div className="p-4 bg-red-100 text-red-700 rounded-lg border border-red-200">
                    {error}
                </div>
            )}

            {successMessage && (
                <div className="p-4 bg-green-100 text-green-700 rounded-lg border border-green-200 animate-fade-in">
                    {successMessage}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Sección Ubicación y Horario */}
                <div className="bg-white p-6 rounded-lg shadow border border-gray-100">
                    <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
                        <Store size={20} className="text-blue-500" />
                        Ubicación y Contacto
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Dirección Física</label>
                            <textarea
                                value={info.direccion || ''}
                                onChange={(e) => handleChange('direccion', e.target.value)}
                                rows={3}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                                placeholder="Ej: Av. Principal..."
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Horario de Atención</label>
                            <input
                                type="text"
                                value={info.horario || ''}
                                onChange={(e) => handleChange('horario', e.target.value)}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                                placeholder="Ej: Lunes a Viernes..."
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono Contacto</label>
                            <input
                                type="text"
                                value={info.telefono_contacto || ''}
                                onChange={(e) => handleChange('telefono_contacto', e.target.value)}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                            />
                        </div>
                    </div>
                </div>

                {/* Sección Logística */}
                <div className="bg-white p-6 rounded-lg shadow border border-gray-100">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
                            <Truck size={20} className="text-green-500" />
                            Logística y Envíos
                        </h3>
                        {/* Master Switch */}
                        <div className="flex items-center">
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={info.has_delivery !== 'false'}
                                    onChange={(e) => handleChange('has_delivery', e.target.checked ? 'true' : 'false')}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                                <span className="ml-3 text-sm font-medium text-gray-700">
                                    {info.has_delivery !== 'false' ? 'Delivery ACTIVO' : 'Delivery INACTIVO'}
                                </span>
                            </label>
                        </div>
                    </div>

                    {info.has_delivery !== 'false' && (
                        <div className="space-y-4 animate-fade-in">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Información de Delivery</label>
                                <textarea
                                    value={info.delivery_info || ''}
                                    onChange={(e) => handleChange('delivery_info', e.target.value)}
                                    rows={2}
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                                    placeholder="¿Hacen delivery? ¿Zonas?"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Precios de Envío</label>
                                <input
                                    type="text"
                                    value={info.delivery_precio || ''}
                                    onChange={(e) => handleChange('delivery_precio', e.target.value)}
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                                    placeholder="Ej: Desde $3 dependiendo la zona"
                                />
                            </div>
                        </div>
                    )}

                    {info.has_delivery === 'false' && (
                        <div className="p-4 bg-gray-50 text-gray-500 text-sm rounded border text-center">
                            El servicio de delivery está desactivado. El bot responderá que solo hay retiro en tienda.
                        </div>
                    )}
                </div>

                {/* Sección Pagos (Full width) */}
                <div className="md:col-span-2 bg-white p-6 rounded-lg shadow border border-gray-100">
                    <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
                        <CreditCard size={20} className="text-purple-500" />
                        Métodos de Pago
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Métodos Aceptados (Texto General)</label>
                            <input
                                type="text"
                                value={info.metodos_pago || ''}
                                onChange={(e) => handleChange('metodos_pago', e.target.value)}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Datos Pago Móvil</label>
                            <textarea
                                value={info.pago_movil || ''}
                                onChange={(e) => handleChange('pago_movil', e.target.value)}
                                rows={2}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none font-mono text-sm"
                                placeholder="Banco, Teléfono, CI"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Datos Zelle</label>
                            <input
                                type="text"
                                value={info.zelle || ''}
                                onChange={(e) => handleChange('zelle', e.target.value)}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Datos Binance</label>
                            <input
                                type="text"
                                value={info.binance || ''}
                                onChange={(e) => handleChange('binance', e.target.value)}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BusinessInfoPage;
