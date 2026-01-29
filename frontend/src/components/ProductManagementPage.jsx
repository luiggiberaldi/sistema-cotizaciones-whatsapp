import React, { useState, useEffect } from 'react';
import { productsAPI } from '../services/api';
import { Trash2, Edit, Plus, Save, X } from 'lucide-react';

export default function ProductManagementPage() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingId, setEditingId] = useState(null);

    // Estado del formulario
    const [formData, setFormData] = useState({
        name: '',
        price: '',
        category: '',
        aliases: ''
    });

    useEffect(() => {
        loadProducts();
    }, []);

    const loadProducts = async () => {
        setLoading(true);
        try {
            const data = await productsAPI.getAll();
            setProducts(data);
            setError(null);
        } catch (err) {
            console.error(err);
            setError('Error cargando productos');
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const resetForm = () => {
        setFormData({ name: '', price: '', category: '', aliases: '' });
        setEditingId(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const productData = {
                name: formData.name,
                price: parseFloat(formData.price),
                category: formData.category,
                aliases: formData.aliases.split(',').map(s => s.trim()).filter(Boolean)
            };

            if (editingId) {
                await productsAPI.update(editingId, productData);
            } else {
                await productsAPI.create(productData);
            }

            await loadProducts();
            resetForm();
        } catch (err) {
            console.error(err);
            setError('Error guardando producto');
        }
    };

    const handleEdit = (product) => {
        setFormData({
            name: product.name,
            price: product.price,
            category: product.category || '',
            aliases: product.aliases ? product.aliases.join(', ') : ''
        });
        setEditingId(product.id);
    };

    const handleDelete = async (id) => {
        if (!window.confirm('¿Seguro que deseas eliminar este producto?')) return;
        try {
            await productsAPI.delete(id);
            await loadProducts();
        } catch (err) {
            console.error(err);
            setError('Error eliminando producto');
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Gestión de Productos</h2>

            {/* Formulario */}
            <form onSubmit={handleSubmit} className="mb-8 bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleInputChange}
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Precio</label>
                        <input
                            type="number"
                            name="price"
                            value={formData.price}
                            onChange={handleInputChange}
                            required
                            step="0.01"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
                        <input
                            type="text"
                            name="category"
                            value={formData.category}
                            onChange={handleInputChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Alias (separados por coma)</label>
                        <input
                            type="text"
                            name="aliases"
                            value={formData.aliases}
                            onChange={handleInputChange}
                            placeholder="Ej: zapatillas, tennis, calzado"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                    </div>
                </div>
                <div className="mt-4 flex justify-end space-x-3">
                    {editingId && (
                        <button
                            type="button"
                            onClick={resetForm}
                            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-md flex items-center"
                        >
                            <X size={18} className="mr-2" /> Cancelar
                        </button>
                    )}
                    <button
                        type="submit"
                        className="px-4 py-2 bg-primary-600 text-white hover:bg-primary-700 rounded-md flex items-center"
                    >
                        {editingId ? <Save size={18} className="mr-2" /> : <Plus size={18} className="mr-2" />}
                        {editingId ? 'Actualizar' : 'Crear'} Producto
                    </button>
                </div>
            </form>

            {/* Error */}
            {error && (
                <div className="bg-red-50 text-red-700 p-3 rounded-md mb-4">
                    {error}
                </div>
            )}

            {/* Tabla */}
            {loading ? (
                <div className="text-center py-8">Cargando...</div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Precio</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoría</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Alias</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {products.map((product) => (
                                <tr key={product.id}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{product.name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${product.price.toFixed(2)}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.category || '-'}</td>
                                    <td className="px-6 py-4 text-sm text-gray-500 truncate max-w-xs">{product.aliases?.join(', ') || '-'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => handleEdit(product)}
                                            className="text-indigo-600 hover:text-indigo-900 mr-4"
                                            title="Editar"
                                        >
                                            <Edit size={18} />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(product.id)}
                                            className="text-red-600 hover:text-red-900"
                                            title="Eliminar"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {products.length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                            No hay productos registrados.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
