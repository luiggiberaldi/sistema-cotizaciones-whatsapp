import React, { useState, useEffect, useCallback } from 'react';
import { Check, X, Loader2, Search, Filter, Users, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { customersAPI } from '../services/api';

const normalizePhone = (phone) => {
    if (!phone) return '';
    // Eliminar +, espacios, guiones y cualquier carácter no numérico
    return phone.toString().replace(/[+\s-]/g, '');
};

const BroadcastListModal = ({ isOpen, onClose, onSend, initialSelectedClients = [] }) => {
    // Configuración de Plantillas
    const TEMPLATES = [
        {
            id: 'pago_recordatorio_es',
            label: '📢 Pago Recordatorio (Genérico)',
            text: 'Hola {{1}}, tu cotización ha sido generada con éxito. Tu monto total es de ${{2}}. La fecha de pago sugerida es el {{3}}. Si tienes dudas, escríbenos.',
            params: ['Nombre del Cliente', 'Monto Total', 'Fecha de Pago Sugerida'],
            defaults: ['{{name}}', '{{total}}', '{{fecha}}']
        },
        {
            id: 'recordatorio_pago_clientes',
            label: '🔔 Recordatorio Pago (Con N° Cotización)',
            text: 'Hola {{1}}, tu cotización N° {{2}} por ${{3}} está lista para pago.',
            params: ['Nombre del Cliente', 'Número de Cotización', 'Monto Total'],
            defaults: ['{{name}}', '{{quote_id}}', '{{total}}'],
            language: 'es_ES'
        }
    ];

    // Estados del Mensaje
    const [selectedTemplateId, setSelectedTemplateId] = useState(TEMPLATES[0].id);
    const [paramValues, setParamValues] = useState({});
    const [languageCode] = useState('es');
    const [sending, setSending] = useState(false);
    const [results, setResults] = useState(null);

    // Estados de Clientes y Filtros
    const [customers, setCustomers] = useState([]);
    const [loadingCustomers, setLoadingCustomers] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [selectedPhones, setSelectedPhones] = useState(new Set(
        initialSelectedClients.map(c => normalizePhone(c.phone))
    ));

    // Obtener plantilla actual
    const currentTemplate = TEMPLATES.find(t => t.id === selectedTemplateId) || TEMPLATES[0];

    // Efecto para cargar valores por defecto al cambiar plantilla
    useEffect(() => {
        if (currentTemplate.defaults) {
            const defaults = {};
            currentTemplate.defaults.forEach((val, index) => {
                defaults[index] = val;
            });
            setParamValues(defaults);
        } else {
            setParamValues({});
        }
    }, [selectedTemplateId]);

    // Cargar clientes con filtros
    const fetchCustomers = useCallback(async () => {
        setLoadingCustomers(true);
        try {
            const data = await customersAPI.list({
                q: searchQuery,
                status: statusFilter
            });
            setCustomers(data);
            if (initialSelectedClients.length > 0 && selectedPhones.size === 0) {
                setSelectedPhones(new Set(initialSelectedClients.map(c => normalizePhone(c.phone))));
            }
        } catch (error) {
            console.error('Error fetching customers:', error);
        } finally {
            setLoadingCustomers(false);
        }
    }, [searchQuery, statusFilter, initialSelectedClients]);

    useEffect(() => {
        if (isOpen) {
            fetchCustomers();
            // Inicializar defaults de la primera plantilla activa
            const defaults = {};
            const t = TEMPLATES.find(t => t.id === selectedTemplateId) || TEMPLATES[0];
            if (t.defaults) {
                t.defaults.forEach((val, idx) => defaults[idx] = val);
                setParamValues(defaults);
            }
        }
    }, [isOpen, fetchCustomers]);

    // Manejo de Selección
    const toggleCustomer = (phone) => {
        const normalized = normalizePhone(phone);
        const newSelected = new Set(selectedPhones);
        if (newSelected.has(normalized)) {
            newSelected.delete(normalized);
        } else {
            newSelected.add(normalized);
        }
        setSelectedPhones(newSelected);
    };

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            const allPhones = customers.map(c => normalizePhone(c.phone_number));
            setSelectedPhones(new Set([...selectedPhones, ...allPhones]));
        } else {
            const currentPhones = new Set(customers.map(c => normalizePhone(c.phone_number)));
            const newSelected = new Set([...selectedPhones].filter(p => !currentPhones.has(p)));
            setSelectedPhones(newSelected);
        }
    };

    const isAllSelected = customers.length > 0 && customers.every(c => selectedPhones.has(normalizePhone(c.phone_number)));

    const handleSend = async () => {
        if (selectedPhones.size === 0) return;
        setSending(true);
        setResults(null);

        try {
            // Convertir objeto paramValues a array ordenado según config de la plantilla
            const paramsToSend = currentTemplate.params.map((_, index) => {
                const val = paramValues[index] || '';
                return val.trim();
            });

            const clientsToSend = [...selectedPhones].map(phone => {
                const customer = customers.find(c => normalizePhone(c.phone_number) === phone);
                const initial = initialSelectedClients.find(c => normalizePhone(c.phone) === phone);
                return {
                    name: customer ? customer.full_name : (initial ? initial.name : 'Cliente'),
                    phone: phone,
                    quote_id: initial ? (parseInt(initial.quote_id) || null) : null
                };
            });

            const result = await onSend(
                clientsToSend,
                selectedTemplateId,
                currentTemplate.language || languageCode,
                paramsToSend
            );
            setResults(result);
        } catch (error) {
            console.error('Error sending broadcast:', error);
            const errorMessage = error.response?.data?.detail || error.message || 'Error desconocido del servidor';
            toast.error('Error al enviar mensajes: ' + errorMessage);
        } finally {
            setSending(false);
        }
    };

    const handleClose = () => {
        setResults(null);
        setSelectedTemplateId(TEMPLATES[0].id);

        // Reset defaults properly on close
        const defaults = {};
        if (TEMPLATES[0].defaults) {
            TEMPLATES[0].defaults.forEach((val, idx) => defaults[idx] = val);
        }
        setParamValues(defaults);

        setSelectedPhones(new Set());
        setSearchQuery('');
        setStatusFilter('');
        onClose();
    };

    // Helper para generar preview
    const getPreviewText = () => {
        let text = currentTemplate.text;

        // Simulación de datos para la preview
        const mockData = {
            '{{name}}': 'Juan Pérez',
            '{{total}}': '$150.00',
            '{{quote_id}}': '1024',
            '{{fecha}}': new Date().toLocaleDateString('es-ES')
        };

        currentTemplate.params.forEach((_, index) => {
            let val = paramValues[index] || `{{${currentTemplate.params[index]}}}`;

            // Si el valor es una variable mágica, mostramos el mock en la preview
            if (mockData[val]) {
                val = mockData[val];
            }

            text = text.replace(`{{${index + 1}}}`, val);
        });
        return text;
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden">
                {/* Header */}
                <div className="px-6 py-4 border-b flex justify-between items-center bg-white shrink-0">
                    <div className="flex items-center gap-2">
                        <div className="bg-primary-100 p-1.5 sm:p-2 rounded-lg">
                            <Users size={20} className="text-primary-600 sm:w-6 sm:h-6" />
                        </div>
                        <h2 className="text-lg sm:text-2xl font-bold text-gray-800">
                            Difusión Masiva v1.1
                        </h2>
                    </div>
                    <button onClick={handleClose} className="text-gray-400 hover:text-gray-600 transition p-2">
                        <X size={24} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 flex flex-col lg:flex-row gap-6">
                    {/* Panel Izquierdo: Configuración y Preview */}
                    <div className="w-full lg:w-96 flex flex-col gap-6 shrink-0 order-2 lg:order-1">
                        <div className="space-y-6">

                            {/* Selector de Plantilla */}
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">
                                    1. Seleccionar Plantilla
                                </label>
                                <div className="space-y-2">
                                    {TEMPLATES.map((t) => (
                                        <label
                                            key={t.id}
                                            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${selectedTemplateId === t.id ? 'border-primary-500 bg-primary-50 shadow-sm' : 'border-gray-200 hover:border-primary-300'}`}
                                        >
                                            <input
                                                type="radio"
                                                name="template"
                                                value={t.id}
                                                checked={selectedTemplateId === t.id}
                                                onChange={() => {
                                                    setSelectedTemplateId(t.id);
                                                    setParamValues({}); // Reset values on change
                                                }}
                                                className="text-primary-600 focus:ring-primary-500"
                                            />
                                            <div className="flex flex-col">
                                                <span className={`text-sm font-medium ${selectedTemplateId === t.id ? 'text-primary-900' : 'text-gray-700'}`}>
                                                    {t.label}
                                                </span>
                                                <span className="text-[10px] text-gray-400">
                                                    ID: {t.id} | Lang: {t.language || 'es'}
                                                </span>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            {/* Inputs Dinámicos */}
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">
                                    2. Variables del Mensaje
                                </label>
                                <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-3">
                                    {currentTemplate.params.length === 0 ? (
                                        <p className="text-xs text-gray-500 italic">Esta plantilla no requiere variables.</p>
                                    ) : (
                                        currentTemplate.params.map((paramLabel, index) => (
                                            <div key={index}>
                                                <label className="block text-xs font-semibold text-gray-600 mb-1">
                                                    {paramLabel} <span className="text-primary-400 font-normal">({`{{${index + 1}}`})</span>
                                                </label>
                                                <input
                                                    type="text"
                                                    value={paramValues[index] || ''}
                                                    onChange={(e) => setParamValues(prev => ({ ...prev, [index]: e.target.value }))}
                                                    placeholder={`Ej: ${paramLabel === 'Nombre del Cliente' ? 'Juan Pérez' : '...'}`}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                                    disabled={sending}
                                                />
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            {/* Preview Card */}
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">
                                    Vista Previa
                                </label>
                                <div className="bg-[#E9EDEF] p-4 rounded-lg border border-gray-200 shadow-inner relative">
                                    <div className="bg-white p-3 rounded-lg shadow-sm rounded-tr-none text-sm text-gray-800 leading-relaxed whitespace-pre-wrap relative">
                                        {getPreviewText()}
                                        <span className="text-[10px] text-gray-400 absolute bottom-1 right-2 block mt-1">
                                            Ahora
                                        </span>
                                    </div>
                                </div>
                            </div>

                        </div>

                        {/* Resultados (Mantenidos abajo a la izquierda) */}
                        {results && (
                            <div className="bg-gray-900 text-white rounded-xl p-4 text-sm max-h-[200px] overflow-y-auto mt-auto">
                                <h4 className="font-bold mb-2 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                    Reporte de Envío
                                </h4>
                                <div className="space-y-1">
                                    {results.results?.map((res, i) => (
                                        <div key={i} className="py-2 border-b border-gray-800 last:border-0">
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="font-medium text-gray-300">...{res.phone.slice(-4)}</span>
                                                {res.success ? (
                                                    <div className="flex items-center gap-1 text-green-400 text-xs">
                                                        <span>Enviado</span>
                                                        <Check size={14} />
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-1 text-red-500 text-xs group relative cursor-help">
                                                        <span>Error</span>
                                                        <X size={14} />

                                                        {/* Tooltip con error completo */}
                                                        <div className="hidden group-hover:block absolute bottom-full right-0 mb-2 w-48 bg-red-900 text-white text-[10px] p-2 rounded shadow-xl z-50 border border-red-700 whitespace-normal">
                                                            {res.error || 'Error desconocido'}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                            {!res.success && (
                                                <button
                                                    onClick={() => toast.error(`Error: ${res.error || 'Sin detalles'}`, { duration: 5000 })}
                                                    className="w-full text-left text-[10px] text-red-300 bg-red-950/50 p-1.5 rounded hover:bg-red-900 transition flex items-start gap-1"
                                                >
                                                    <AlertTriangle size={12} className="mt-0.5 shrink-0" />
                                                    <span className="truncate">{res.error || 'Click para ver detalles'}</span>
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Panel Derecho: Selección de Clientes (Expandido) */}
                    <div className="flex-1 flex flex-col space-y-4 order-1 lg:order-2 h-full min-h-[400px]">
                        <div className="flex flex-col sm:flex-row gap-3 bg-white p-1">
                            {/* Búsqueda */}
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
                                <input
                                    type="text"
                                    placeholder="Buscar cliente..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                                />
                            </div>
                            {/* Filtro Status */}
                            <div className="relative shrink-0">
                                <Filter className="absolute left-3 top-2.5 text-gray-400" size={18} />
                                <select
                                    value={statusFilter}
                                    onChange={(e) => setStatusFilter(e.target.value)}
                                    className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white"
                                >
                                    <option value="">Todos</option>
                                    <option value="draft">Borradores</option>
                                    <option value="approved">Aprobados</option>
                                </select>
                            </div>
                        </div>

                        {/* Select All Bar */}
                        <div className="bg-gray-50 px-4 py-2 rounded-lg border border-gray-200 flex items-center justify-between">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={isAllSelected}
                                    onChange={handleSelectAll}
                                    className="w-4 h-4 text-primary-600 rounded"
                                />
                                <span className="text-sm font-semibold text-gray-700">Seleccionar Todo</span>
                            </label>
                            <span className="bg-white border border-gray-200 text-gray-600 px-2 py-0.5 rounded text-xs font-bold">
                                {selectedPhones.size} / {customers.length}
                            </span>
                        </div>

                        {/* Lista Scrollable */}
                        <div className="flex-1 overflow-y-auto border border-gray-200 rounded-xl bg-white shadow-sm">
                            {loadingCustomers ? (
                                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                    <Loader2 className="animate-spin mb-2" size={32} />
                                    <p>Cargando...</p>
                                </div>
                            ) : customers.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                                    <Users size={48} className="mb-2 opacity-20" />
                                    <p>No hay resultados.</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-gray-100">
                                    {customers.map((customer) => (
                                        <label
                                            key={customer.phone_number}
                                            className={`flex items-center gap-3 px-4 py-3 hover:bg-gray-50 cursor-pointer transition ${selectedPhones.has(normalizePhone(customer.phone_number)) ? 'bg-blue-50/50' : ''}`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedPhones.has(normalizePhone(customer.phone_number))}
                                                onChange={() => toggleCustomer(customer.phone_number)}
                                                className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                            />
                                            <div className="flex-1">
                                                <p className="font-bold text-gray-900">{customer.full_name}</p>
                                                <p className="text-xs text-gray-500 font-mono">{customer.phone_number}</p>
                                            </div>
                                            {selectedPhones.has(normalizePhone(customer.phone_number)) && (
                                                <span className="w-2 h-2 rounded-full bg-primary-500"></span>
                                            )}
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-gray-50 border-t flex flex-col sm:flex-row justify-between items-center gap-4 shrink-0">
                    <p className="text-sm text-gray-500 italic">
                        Los mensajes se enviarán vía la API oficial de WhatsApp Cloud.
                    </p>
                    <div className="flex gap-3 w-full sm:w-auto">
                        <button
                            onClick={handleClose}
                            className="flex-1 sm:flex-none px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition font-bold text-gray-700"
                            disabled={sending}
                        >
                            Cancelar
                        </button>
                        <button
                            onClick={handleSend}
                            disabled={sending || selectedPhones.size === 0}
                            className="flex-1 sm:flex-none px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-bold shadow-lg shadow-primary-200 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {sending ? (
                                <>
                                    <Loader2 className="animate-spin" size={20} />
                                    Procesando...
                                </>
                            ) : (
                                <>Iniciar Difusión ({selectedPhones.size})</>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BroadcastListModal;

