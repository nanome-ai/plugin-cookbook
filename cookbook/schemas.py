import itertools
import logging
from marshmallow import Schema, fields, post_load, ValidationError
from nanome.api import structure
from nanome.util import Vector3, Quaternion


logging = logging.getLogger(__name__)

class StreamSchema(Schema):
    stream_id = fields.Integer(required=True)
    error = fields.Integer()

class QuaternionField(fields.Field):

    def _serialize(self, value: Vector3, attr, obj, **kwargs):
        return [value.x, value.y, value.z, value.w]

    def _deserialize(self, value, attr, data, **kwargs):
        if len(value) != 4:
            raise ValidationError("Quaternion must contain 4 values")
        return Quaternion(*value)


class Vector3Field(fields.Field):

    def _serialize(self, value, attr, obj, **kwargs):
        output = list(value.unpack())
        return output

    def _deserialize(self, value, attr, data, **kwargs):
        return Vector3(*value)


class AtomSchema(Schema):
    index = fields.Integer(required=True)
    selected = fields.Boolean()
    labeled = fields.Boolean()
    atom_rendering = fields.Boolean()
    surface_rendering = fields.Boolean()
    exists = fields.Boolean()
    is_het = fields.Boolean()
    occupancy = fields.Boolean()
    bfactor = fields.Boolean()
    acceptor = fields.Boolean()
    donor = fields.Boolean()
    polar_hydrogen = fields.Boolean()
    atom_mode = fields.Integer()  # Enum, see nanome.util.enums.AtomRenderingMode
    serial = fields.Integer()
    current_conformer = fields.Integer(load_only=True)
    conformer_count = fields.Integer(load_only=True)
    positions = fields.List(Vector3Field())
    label_text = fields.String()
    atom_color = fields.String()
    atom_scale = fields.Float()
    surface_color = fields.Str()  # Hex color
    symbol = fields.Str()
    name = fields.Str()
    position = Vector3Field()
    formal_charge = fields.Float()
    partial_charge = fields.Float()
    vdw_radius = fields.Float(load_only=True)
    alt_loc = fields.Str(max=1)

    @post_load
    def make_atom(self, data, **kwargs):
        new_obj = structure.Atom()
        for key in data:
            try:
                setattr(new_obj, key, data[key])
            except AttributeError:
                raise AttributeError('Could not set attribute {}'.format(key))
        return new_obj

class BondSchema(Schema):
    index = fields.Integer(required=True)
    atom1 = AtomSchema(only=('index',))
    atom2 = AtomSchema(only=('index',))
    kind = fields.Integer()  # Enum, see nanome.util.enums.Kind

    @post_load
    def make_bond(self, data, **kwargs):
        new_obj = structure.Bond()
        for key in data:
            try:
                setattr(new_obj, key, data[key])
            except AttributeError:
                raise AttributeError('Could not set attribute {}'.format(key))
        return new_obj


class ResidueSchema(Schema):
    index = fields.Integer(required=True)
    atoms = fields.List(fields.Nested(AtomSchema))
    bonds = fields.List(fields.Nested(BondSchema))
    ribboned = fields.Boolean()
    ribbon_size = fields.Float()
    ribbon_mode = fields.Integer()  # Enum, see nanome.util.enums.RibbonMode
    ribbon_color = fields.Str() # hex code
    labeled = fields.Boolean()
    label_text = fields.Str()
    type = fields.Str()
    serial = fields.Integer()
    name = fields.Str()
    secondary_structure = fields.Integer() # Enum, see nanome.util.enums.SecondaryStructure
    ignored_alt_locs = fields.List(fields.Str())

    @post_load
    def make_residue(self, data, **kwargs):
        new_obj = structure.Residue()
        for key in data:
            try:
                setattr(new_obj, key, data[key])
            except AttributeError:
                raise AttributeError('Could not set attribute {}'.format(key))
        for child in itertools.chain(new_obj.atoms, new_obj.bonds):
            child._parent = new_obj

        return new_obj


class ChainSchema(Schema):
    index = fields.Integer(required=True)
    name = fields.Str()
    residues = fields.Nested(ResidueSchema, many=True)

    @post_load
    def make_chain(self, data, **kwargs):
        new_obj = structure.Chain()
        for key in data:
            try:
                setattr(new_obj, key, data[key])
            except AttributeError:
                raise AttributeError('Could not set attribute {}'.format(key))
        for child in new_obj.residues:
            child._parent = new_obj
        return new_obj


class MoleculeSchema(Schema):
    index = fields.Integer(default=-1)
    chains = fields.List(fields.Nested(ChainSchema))
    name = fields.Str()
    associated = fields.List(fields.Str())
    conformer_count = fields.Integer(load_only=True)
    current_conformer = fields.Integer()

    @post_load
    def make_molecule(self, data, **kwargs):
        new_obj = structure.Molecule()
        for key in data:
            try:
                setattr(new_obj, key, data[key])
            except AttributeError:
                raise AttributeError('Could not set attribute {}'.format(key))
        for child in new_obj.chains:
            child._parent = new_obj
        return new_obj


class ComplexSchema(Schema):
    index = fields.Integer(required=True)
    boxed = fields.Boolean()
    locked = fields.Boolean()
    visible = fields.Boolean()
    computing = fields.Boolean()
    box_label = fields.String()
    name = fields.Str()
    index_tag = fields.Integer()
    split_tag = fields.Str()
    position = Vector3Field()
    rotation = QuaternionField()
    molecules = fields.List(fields.Nested(MoleculeSchema))

    @post_load
    def make_complex(self, data, **kwargs):
        new_obj = structure.Complex()
        for key in data:
            try:
                setattr(new_obj, key, data[key])
            except AttributeError:
                raise AttributeError('Could not set attribute {}'.format(key))

        for child in new_obj.molecules:
            child._parent = new_obj
        return new_obj


class WorkspaceSchema(Schema):
    complexes = fields.List(fields.Nested(ComplexSchema))
    position = Vector3Field()
    rotation = QuaternionField()
    scale = Vector3Field()

    @post_load
    def make_workspace(self, data, **kwargs):
        new_obj = structure.Workspace()
        for key in data:
            try:
                setattr(new_obj, key, data[key])
            except AttributeError:
                raise AttributeError('Could not set attribute {}'.format(key))
        return new_obj


structure_schema_map = {
    structure.Atom: AtomSchema(),
    structure.Bond: BondSchema(),
    structure.Residue: ResidueSchema(),
    structure.Chain: ChainSchema(),
    structure.Molecule: MoleculeSchema(),
    structure.Complex: ComplexSchema(),
}

function_arg_schemas = {
    'request_workspace':{
        'params': [],
        'output': WorkspaceSchema()
    },
    'request_complexes': {
        'params': [fields.List(fields.Integer)],
        'output': ComplexSchema(many=True)
    },
    'update_structures_shallow': {
        'params': [ComplexSchema(many=True)],
        'output': None
    }, 
    'request_complex_list': {
        'params': [fields.List(fields.Integer)],
        'output': ComplexSchema(many=True)
    },
    'create_writing_stream': {
        'params': [fields.List(fields.Integer), fields.Integer()],
        'output': StreamSchema()
    },
    'stream_update': {
        'params': [fields.Integer(), fields.List(fields.Integer)],
        'output': None
    }
}
