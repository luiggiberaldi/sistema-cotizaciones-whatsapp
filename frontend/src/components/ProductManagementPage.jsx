import React, { useState, useEffect, useMemo } from 'react';
import { productsAPI } from '../services/api';
import { Trash2, Edit, Plus, Save, X, LayoutGrid, List as ListIcon, Search, ShoppingBag } from 'lucide-react';

export default function ProductManagementPage() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingId, setEditingId] = useState(null);

    // Estados de UI
    const [viewMode, setViewMode] = useState('gallery'); // 'list' | 'gallery'
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('Todos');


    // Estado del formulario
    const [formData, setFormData] = useState({
        name: '',
        price: '',
        category: '',
        aliases: '',
        image_url: ''
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
        setFormData({ name: '', price: '', category: '', aliases: '', image_url: '' });
        setEditingId(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const productData = {
                name: formData.name,
                price: parseFloat(formData.price),
                category: formData.category,
                aliases: formData.aliases.split(',').map(s => s.trim()).filter(Boolean),
                image_url: formData.image_url || null
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
            aliases: product.aliases ? product.aliases.join(', ') : '',
            image_url: product.image_url || ''
        });
        setEditingId(product.id);
        // Scroll al formulario si está muy abajo
        window.scrollTo({ top: 0, behavior: 'smooth' });
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

    const handleDeleteAll = async () => {
        if (!window.confirm('⚠️ ¿ESTÁS SEGURO? Esto eliminará TODOS los productos del inventario. Esta acción no se puede deshacer.')) return;

        // Doble confirmación para seguridad
        if (!window.confirm('Por favor confirma de nuevo: ¿Eliminar TODO el inventario permanentemente?')) return;

        setLoading(true);
        try {
            // Eliminamos uno por uno (o idealmente un endpoint masivo si existiera)
            // Como no tenemos endpoint masivo expuesto en api.js, lo hacemos iterando
            // Nota: Para grandes inventarios esto debería ser un endpoint de backend
            const deletePromises = products.map(p => productsAPI.delete(p.id));
            await Promise.all(deletePromises);

            await loadProducts();
            setError(null);
            alert('Inventario eliminado correctamente.');
        } catch (err) {
            console.error(err);
            setError('Error eliminando inventario masivo');
        } finally {
            setLoading(false);
        }
    };

    // --- Lógica de Filtrado ---
    const categories = useMemo(() => {
        const cats = new Set(products.map(p => p.category).filter(Boolean));
        return ['Todos', ...Array.from(cats).sort()];
    }, [products]);

    const filteredProducts = useMemo(() => {
        return products.filter(product => {
            const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                (product.aliases && product.aliases.some(a => a.toLowerCase().includes(searchTerm.toLowerCase())));
            const matchesCategory = selectedCategory === 'Todos' || product.category === selectedCategory;
            return matchesSearch && matchesCategory;
        });
    }, [products, searchTerm, selectedCategory]);



    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 min-h-screen relative pb-32">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                    <ShoppingBag className="mr-2 text-primary-600" /> Catálogo de Productos
                </h2>

                {/* Controles de Vista */}
                <div className="flex gap-3">
                    {/* Botón Eliminar Todo */}
                    <button
                        onClick={handleDeleteAll}
                        className="flex items-center gap-2 px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition border border-red-200 text-sm font-medium"
                        title="Eliminar todo el inventario"
                    >
                        <Trash2 size={16} />
                        <span className="hidden md:inline">Eliminar Todo</span>
                    </button>

                    <div className="flex bg-gray-100 p-1 rounded-lg">
                        <button
                            onClick={() => setViewMode('list')}
                            className={`p-2 rounded-md transition ${viewMode === 'list' ? 'bg-white shadow text-primary-600' : 'text-gray-500 hover:text-gray-900'}`}
                            title="Vista de Lista"
                        >
                            <ListIcon size={20} />
                        </button>
                        <button
                            onClick={() => setViewMode('gallery')}
                            className={`p-2 rounded-md transition ${viewMode === 'gallery' ? 'bg-white shadow text-primary-600' : 'text-gray-500 hover:text-gray-900'}`}
                            title="Vista de Galería"
                        >
                            <LayoutGrid size={20} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Formulario (Colapsable o siempre visible? Por ahora siempre visible para gestión) */}
            <div className={`mb-8 bg-gray-50 p-6 rounded-xl border border-gray-200 transition-all ${editingId ? 'ring-2 ring-primary-500' : ''}`}>
                <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center">
                    {editingId ? <Edit size={18} className="mr-2" /> : <Plus size={18} className="mr-2" />}
                    {editingId ? 'Editar Producto' : 'Agregar Nuevo Producto'}
                </h3>
                <form onSubmit={handleSubmit}>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="col-span-1 md:col-span-2">
                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Nombre</label>
                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleInputChange}
                                required
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                placeholder="Ej: Laptop HP Pavilion"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Precio ($)</label>
                            <input
                                type="number"
                                name="price"
                                value={formData.price}
                                onChange={handleInputChange}
                                required
                                step="0.01"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                placeholder="0.00"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Categoría</label>
                            <input
                                type="text"
                                name="category"
                                value={formData.category}
                                onChange={handleInputChange}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                placeholder="Ej: Computación"
                            />
                        </div>
                        <div className="col-span-1 md:col-span-2">
                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">URL de Imagen</label>
                            <input
                                type="text"
                                name="image_url"
                                value={formData.image_url}
                                onChange={handleInputChange}
                                placeholder="https://..."
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                        </div>
                        <div className="col-span-1 md:col-span-2">
                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Alias (búsqueda)</label>
                            <input
                                type="text"
                                name="aliases"
                                value={formData.aliases}
                                onChange={handleInputChange}
                                placeholder="Separados por coma"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                        </div>
                    </div>
                    <div className="mt-4 flex justify-end gap-3">
                        {editingId && (
                            <button
                                type="button"
                                onClick={resetForm}
                                className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg font-medium flex items-center transition"
                            >
                                <X size={18} className="mr-1" /> Cancelar
                            </button>
                        )}
                        <button
                            type="submit"
                            className="px-6 py-2 bg-primary-600 text-white hover:bg-primary-700 rounded-lg font-medium flex items-center shadow-md transition transform hover:-translate-y-0.5"
                        >
                            <Save size={18} className="mr-2" />
                            {editingId ? 'Actualizar Producto' : 'Guardar Producto'}
                        </button>
                    </div>
                </form>
            </div>

            {/* Barra de Herramientas de Catálogo */}
            <div className="flex flex-col gap-4 mb-6">
                {/* Buscador */}
                <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                        type="text"
                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm shadow-sm"
                        placeholder="Buscar por nombre, categoría o alias..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                {/* Categorías (Chips) */}
                <div className="flex flex-wrap gap-2">
                    {categories.map(cat => (
                        <button
                            key={cat}
                            onClick={() => setSelectedCategory(cat)}
                            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${selectedCategory === cat
                                ? 'bg-primary-600 text-white shadow'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            {cat}
                        </button>
                    ))}
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6 border border-red-200">
                    {error}
                </div>
            )}

            {/* Contenido Principal */}
            {loading ? (
                <div className="flex justify-center items-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
                </div>
            ) : filteredProducts.length === 0 ? (
                <div className="text-center py-20 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                    <ShoppingBag className="mx-auto h-12 w-12 text-gray-300 mb-3" />
                    <p className="text-gray-500 text-lg">No se encontraron productos.</p>
                    <button onClick={() => { setSearchTerm(''); setSelectedCategory('Todos'); }} className="mt-2 text-primary-600 hover:underline">
                        Limpiar filtros
                    </button>
                </div>
            ) : (
                <>
                    {viewMode === 'list' && (
                        <div className="overflow-x-auto bg-white rounded-xl border border-gray-200 shadow-sm">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Producto</th>
                                        <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Categoría</th>
                                        <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Precio</th>
                                        <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {filteredProducts.map((product) => {
                                        const qty = cart[product.id] || 0;
                                        return (
                                            <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center">
                                                        <div className="flex-shrink-0 h-12 w-12 bg-gray-100 rounded-lg overflow-hidden border border-gray-200">
                                                            {product.image_url ? (
                                                                <img src={product.image_url} alt={product.name} className="h-full w-full object-cover" />
                                                            ) : (
                                                                <div className="h-full w-full flex items-center justify-center text-gray-400"><ShoppingBag size={20} /></div>
                                                            )}
                                                        </div>
                                                        <div className="ml-4">
                                                            <div className="text-sm font-medium text-gray-900">{product.name}</div>
                                                            <div className="text-xs text-gray-500 truncate max-w-[200px]">{product.aliases?.join(', ')}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                                                        {product.category || 'General'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                                                    ${product.price.toFixed(2)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                    <div className="flex items-center justify-end gap-2">
                                                        <button onClick={() => handleEdit(product)} className="text-indigo-600 hover:text-indigo-900 p-2 hover:bg-indigo-50 rounded-full transition">
                                                            <Edit size={18} />
                                                        </button>
                                                        <button onClick={() => handleDelete(product.id)} className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded-full transition">
                                                            <Trash2 size={18} />
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {viewMode === 'gallery' && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            {filteredProducts.map((product) => {
                                return (
                                    <div key={product.id} className="group bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-200 overflow-hidden flex flex-col">
                                        {/* Imagen */}
                                        <div className="relative aspect-square bg-gray-100 overflow-hidden">
                                            {product.image_url ? (
                                                <img
                                                    src={product.image_url}
                                                    alt={product.name}
                                                    className="h-full w-full object-cover group-hover:scale-110 transition-transform duration-500"
                                                />
                                            ) : (
                                                <div className="h-full w-full flex items-center justify-center text-gray-300">
                                                    <ShoppingBag size={48} />
                                                </div>
                                            )}
                                            {/* Overlay de acciones rápidas */}
                                            <div className="absolute top-2 right-2 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                                <button
                                                    onClick={() => handleEdit(product)}
                                                    className="p-2 bg-white/90 backdrop-blur-sm rounded-full shadow hover:bg-white text-indigo-600 transition"
                                                    title="Editar"
                                                >
                                                    <Edit size={16} />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(product.id)}
                                                    className="p-2 bg-white/90 backdrop-blur-sm rounded-full shadow hover:bg-white text-red-600 transition"
                                                    title="Eliminar"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>

                                        </div>

                                        {/* Contenido */}
                                        <div className="p-4 flex flex-col flex-grow">
                                            <div className="text-xs font-semibold text-primary-600 uppercase tracking-widest mb-1">
                                                {product.category || 'General'}
                                            </div>
                                            <h3 className="font-bold text-gray-900 leading-tight mb-2 line-clamp-2" title={product.name}>
                                                {product.name}
                                            </h3>
                                            <div className="mt-auto pt-3 border-t border-gray-100 flex items-center justify-between">
                                                <span className="text-xl font-extrabold text-gray-900">
                                                    ${product.price.toFixed(2)}
                                                </span>


                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </>
            )}

        </div>
    );
}
