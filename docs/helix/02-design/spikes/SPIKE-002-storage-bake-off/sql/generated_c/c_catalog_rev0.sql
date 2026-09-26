INSERT INTO c.schema_rev VALUES (0,'0.7.0','d7e93e9cc53b5dfcc23ba553d5d9e7122e8a3276fd5ab6069f1db540fc3f2409','{
 "umf": "0.7.0",
 "id": "truss-spike-002-sales",
 "vocabularies": {
  "umf.ddd": {
   "version": "0.1.0"
  }
 },
 "modules": [
  {
   "id": "sales",
   "namespace": "sales",
   "extensions": {
    "umf.ddd": {
     "kind": "bounded-context",
     "terms": []
    }
   },
   "elements": [
    {
     "id": "Customer",
     "kind": "record",
     "members": [
      {
       "module": "sales",
       "element": "Customer.id"
      },
      {
       "module": "sales",
       "element": "Customer.code"
      },
      {
       "module": "sales",
       "element": "Customer.name"
      },
      {
       "module": "sales",
       "element": "Customer.email"
      },
      {
       "module": "sales",
       "element": "Customer.createdAt"
      },
      {
       "module": "sales",
       "element": "Customer.tags"
      },
      {
       "module": "sales",
       "element": "Customer.attributes"
      },
      {
       "module": "sales",
       "element": "Customer.address"
      }
     ],
     "extensions": {
      "umf.ddd": {
       "kind": "entity",
       "fields": {
        "id": {
         "type": {
          "kind": "scalar",
          "name": "integer"
         },
         "cardinality": "one"
        },
        "code": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "one"
        },
        "name": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "one"
        },
        "email": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "optional"
        },
        "createdAt": {
         "type": {
          "kind": "scalar",
          "name": "date-time"
         },
         "cardinality": "one"
        },
        "tags": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "many"
        },
        "attributes": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "optional",
         "description": "core: map<string,string>; DDD has no map cardinality (truss-local stand-in)"
        },
        "address": {
         "type": {
          "kind": "concept",
          "target": {
           "module": "sales",
           "element": "Address"
          }
         },
         "cardinality": "optional"
        }
       },
       "identity": {
        "fields": [
         "id"
        ],
        "scope": "context"
       }
      }
     },
     "keys": [
      {
       "id": "identity",
       "name": "Identity",
       "fields": [
        {
         "module": "sales",
         "element": "Customer.id"
        }
       ],
       "primary": true
      },
      {
       "id": "account-code",
       "name": "Account code",
       "fields": [
        {
         "module": "sales",
         "element": "Customer.code"
        }
       ]
      }
     ]
    },
    {
     "id": "Customer.id",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "integer",
     "facets": {
      "integerWidth": {
       "bits": 64,
       "signed": true
      }
     }
    },
    {
     "id": "Customer.code",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 20,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Customer.name",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 100,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Customer.email",
     "kind": "field",
     "nullability": "absent-allowed",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 200,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Customer.createdAt",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "timestamp"
    },
    {
     "id": "Customer.tags",
     "kind": "field",
     "nullability": "absent-allowed",
     "cardinality": "array",
     "extensions": {},
     "itemType": {
      "module": "sales",
      "element": "Customer.tags.item"
     }
    },
    {
     "id": "Customer.tags.item",
     "kind": "field",
     "scalarType": "string",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "facets": {
      "length": {
       "max": 30,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Customer.attributes",
     "kind": "field",
     "nullability": "absent-allowed",
     "cardinality": "map",
     "extensions": {},
     "itemType": {
      "module": "sales",
      "element": "Customer.attributes.item"
     }
    },
    {
     "id": "Customer.attributes.item",
     "kind": "field",
     "scalarType": "string",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "facets": {
      "length": {
       "max": 100,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Customer.address",
     "kind": "field",
     "nullability": "absent-allowed",
     "cardinality": "one",
     "extensions": {},
     "references": [
      {
       "role": "record-type",
       "module": "sales",
       "element": "Address"
      }
     ]
    },
    {
     "id": "Address",
     "kind": "record",
     "members": [
      {
       "module": "sales",
       "element": "Address.street"
      },
      {
       "module": "sales",
       "element": "Address.city"
      },
      {
       "module": "sales",
       "element": "Address.postalCode"
      },
      {
       "module": "sales",
       "element": "Address.country"
      }
     ],
     "extensions": {
      "umf.ddd": {
       "kind": "value",
       "fields": {
        "street": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "one"
        },
        "city": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "one"
        },
        "postalCode": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "optional"
        },
        "country": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "one"
        }
       },
       "equality": {
        "fields": [
         "street",
         "city",
         "postalCode",
         "country"
        ]
       }
      }
     }
    },
    {
     "id": "Address.street",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 200,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Address.city",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 100,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Address.postalCode",
     "kind": "field",
     "nullability": "absent-allowed",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 20,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Address.country",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 2,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Order",
     "kind": "record",
     "members": [
      {
       "module": "sales",
       "element": "Order.id"
      },
      {
       "module": "sales",
       "element": "Order.placedAt"
      },
      {
       "module": "sales",
       "element": "Order.status"
      },
      {
       "module": "sales",
       "element": "Order.channel"
      },
      {
       "module": "sales",
       "element": "Order.total"
      }
     ],
     "extensions": {
      "umf.ddd": {
       "kind": "entity",
       "fields": {
        "id": {
         "type": {
          "kind": "scalar",
          "name": "integer"
         },
         "cardinality": "one"
        },
        "placedAt": {
         "type": {
          "kind": "scalar",
          "name": "date-time"
         },
         "cardinality": "one"
        },
        "status": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "one"
        },
        "channel": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "optional"
        },
        "total": {
         "type": {
          "kind": "scalar",
          "name": "decimal"
         },
         "cardinality": "one"
        },
        "customerId": {
         "type": {
          "kind": "scalar",
          "name": "integer"
         },
         "cardinality": "one",
         "description": "FK carrier stand-in for a core relationship"
        }
       },
       "identity": {
        "fields": [
         "id"
        ],
        "scope": "context"
       }
      }
     },
     "keys": [
      {
       "id": "identity",
       "name": "Identity",
       "fields": [
        {
         "module": "sales",
         "element": "Order.id"
        }
       ],
       "primary": true
      }
     ]
    },
    {
     "id": "Order.id",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "integer",
     "facets": {
      "integerWidth": {
       "bits": 64,
       "signed": true
      }
     }
    },
    {
     "id": "Order.placedAt",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "timestamp"
    },
    {
     "id": "Order.status",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 20,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Order.channel",
     "kind": "field",
     "nullability": "absent-allowed",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 20,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Order.total",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "decimal",
     "facets": {
      "precision": 14,
      "scale": 2
     }
    },
    {
     "id": "OrderLine",
     "kind": "record",
     "members": [
      {
       "module": "sales",
       "element": "OrderLine.id"
      },
      {
       "module": "sales",
       "element": "OrderLine.lineNo"
      },
      {
       "module": "sales",
       "element": "OrderLine.quantity"
      },
      {
       "module": "sales",
       "element": "OrderLine.unitPrice"
      },
      {
       "module": "sales",
       "element": "OrderLine.lineTotal"
      }
     ],
     "extensions": {
      "umf.ddd": {
       "kind": "entity",
       "fields": {
        "id": {
         "type": {
          "kind": "scalar",
          "name": "integer"
         },
         "cardinality": "one"
        },
        "lineNo": {
         "type": {
          "kind": "scalar",
          "name": "integer"
         },
         "cardinality": "one"
        },
        "quantity": {
         "type": {
          "kind": "scalar",
          "name": "integer"
         },
         "cardinality": "one"
        },
        "unitPrice": {
         "type": {
          "kind": "scalar",
          "name": "decimal"
         },
         "cardinality": "one"
        },
        "lineTotal": {
         "type": {
          "kind": "scalar",
          "name": "decimal"
         },
         "cardinality": "one"
        },
        "orderId": {
         "type": {
          "kind": "scalar",
          "name": "integer"
         },
         "cardinality": "one",
         "description": "FK carrier stand-in for a core relationship"
        },
        "productId": {
         "type": {
          "kind": "scalar",
          "name": "integer"
         },
         "cardinality": "one",
         "description": "FK carrier stand-in for a core relationship"
        }
       },
       "identity": {
        "fields": [
         "id"
        ],
        "scope": "context"
       },
       "invariants": [
        {
         "id": "line-total",
         "scope": "definition",
         "language": "postgresql",
         "version": "17",
         "expression": "\"lineTotal\" = \"quantity\" * \"unitPrice\"",
         "references": [
          {
           "module": "sales",
           "element": "OrderLine"
          }
         ]
        }
       ]
      }
     },
     "keys": [
      {
       "id": "identity",
       "name": "Identity",
       "fields": [
        {
         "module": "sales",
         "element": "OrderLine.id"
        }
       ],
       "primary": true
      }
     ]
    },
    {
     "id": "OrderLine.id",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "integer",
     "facets": {
      "integerWidth": {
       "bits": 64,
       "signed": true
      }
     }
    },
    {
     "id": "OrderLine.lineNo",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "integer",
     "facets": {
      "integerWidth": {
       "bits": 16,
       "signed": true
      }
     }
    },
    {
     "id": "OrderLine.quantity",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "integer",
     "facets": {
      "integerWidth": {
       "bits": 32,
       "signed": true
      }
     }
    },
    {
     "id": "OrderLine.unitPrice",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "decimal",
     "facets": {
      "precision": 12,
      "scale": 2
     }
    },
    {
     "id": "OrderLine.lineTotal",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "decimal",
     "facets": {
      "precision": 14,
      "scale": 2
     }
    },
    {
     "id": "Product",
     "kind": "record",
     "members": [
      {
       "module": "sales",
       "element": "Product.id"
      },
      {
       "module": "sales",
       "element": "Product.sku"
      },
      {
       "module": "sales",
       "element": "Product.name"
      },
      {
       "module": "sales",
       "element": "Product.price"
      },
      {
       "module": "sales",
       "element": "Product.image"
      }
     ],
     "extensions": {
      "umf.ddd": {
       "kind": "entity",
       "fields": {
        "id": {
         "type": {
          "kind": "scalar",
          "name": "integer"
         },
         "cardinality": "one"
        },
        "sku": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "one"
        },
        "name": {
         "type": {
          "kind": "scalar",
          "name": "string"
         },
         "cardinality": "one"
        },
        "price": {
         "type": {
          "kind": "scalar",
          "name": "decimal"
         },
         "cardinality": "one"
        },
        "image": {
         "type": {
          "kind": "scalar",
          "name": "bytes"
         },
         "cardinality": "optional"
        }
       },
       "identity": {
        "fields": [
         "id"
        ],
        "scope": "context"
       }
      }
     },
     "keys": [
      {
       "id": "identity",
       "name": "Identity",
       "fields": [
        {
         "module": "sales",
         "element": "Product.id"
        }
       ],
       "primary": true
      }
     ]
    },
    {
     "id": "Product.id",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "integer",
     "facets": {
      "integerWidth": {
       "bits": 64,
       "signed": true
      }
     }
    },
    {
     "id": "Product.sku",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 32,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Product.name",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "string",
     "facets": {
      "length": {
       "max": 200,
       "unit": "unicode-scalar"
      }
     }
    },
    {
     "id": "Product.price",
     "kind": "field",
     "nullability": "required",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "decimal",
     "facets": {
      "precision": 12,
      "scale": 2
     }
    },
    {
     "id": "Product.image",
     "kind": "field",
     "nullability": "absent-allowed",
     "cardinality": "one",
     "extensions": {},
     "scalarType": "binary",
     "facets": {
      "length": {
       "max": 65536,
       "unit": "byte"
      }
     }
    }
   ],
   "relationships": [
    {
     "id": "order-customer",
     "name": "customer",
     "source": [
      {
       "module": "sales",
       "element": "Order"
      }
     ],
     "target": [
      {
       "module": "sales",
       "element": "Customer",
       "key": "identity"
      }
     ],
     "sourceMultiplicity": {
      "min": 0,
      "max": "*"
     },
     "targetMultiplicity": {
      "min": 1,
      "max": 1
     },
     "targetLifecycle": "independent",
     "directed": true,
     "inverse": "orders"
    },
    {
     "id": "order-lines",
     "name": "lines",
     "source": [
      {
       "module": "sales",
       "element": "Order"
      }
     ],
     "target": [
      {
       "module": "sales",
       "element": "OrderLine",
       "key": "identity"
      }
     ],
     "sourceMultiplicity": {
      "min": 1,
      "max": 1
     },
     "targetMultiplicity": {
      "min": 1,
      "max": "*"
     },
     "targetLifecycle": "owned",
     "directed": true,
     "inverse": "order"
    },
    {
     "id": "line-product",
     "name": "product",
     "source": [
      {
       "module": "sales",
       "element": "OrderLine"
      }
     ],
     "target": [
      {
       "module": "sales",
       "element": "Product",
       "key": "identity"
      }
     ],
     "sourceMultiplicity": {
      "min": 0,
      "max": "*"
     },
     "targetMultiplicity": {
      "min": 1,
      "max": 1
     },
     "targetLifecycle": "independent",
     "directed": true,
     "inverse": "orderLines"
    }
   ]
  }
 ],
 "extensions": {}
}
');
INSERT INTO c.type_def VALUES (1,'sales','Customer','record') ON CONFLICT (type_id) DO NOTHING;
INSERT INTO c.type_def VALUES (2,'sales','Address','record') ON CONFLICT (type_id) DO NOTHING;
INSERT INTO c.type_def VALUES (3,'sales','Order','record') ON CONFLICT (type_id) DO NOTHING;
INSERT INTO c.type_def VALUES (4,'sales','OrderLine','record') ON CONFLICT (type_id) DO NOTHING;
INSERT INTO c.type_def VALUES (5,'sales','Product','record') ON CONFLICT (type_id) DO NOTHING;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (1,1,'Customer.id','id','integer','required','one','{"integerWidth":{"bits":64,"signed":true}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (2,1,'Customer.code','code','string','required','one','{"length":{"max":20,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (3,1,'Customer.name','name','string','required','one','{"length":{"max":100,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (4,1,'Customer.email','email','string','absent-allowed','one','{"length":{"max":200,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (5,1,'Customer.createdAt','createdAt','timestamp','required','one',NULL,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (6,1,'Customer.tags','tags',NULL,'absent-allowed','array',NULL,'{"scalar":"string","facets":{"length":{"max":30,"unit":"unicode-scalar"}}}'::jsonb,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (7,1,'Customer.attributes','attributes',NULL,'absent-allowed','map',NULL,'{"scalar":"string","facets":{"length":{"max":100,"unit":"unicode-scalar"}}}'::jsonb,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (8,2,'Address.street','street','string','required','one','{"length":{"max":200,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (9,2,'Address.city','city','string','required','one','{"length":{"max":100,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (10,2,'Address.postalCode','postalCode','string','absent-allowed','one','{"length":{"max":20,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (11,2,'Address.country','country','string','required','one','{"length":{"max":2,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (12,3,'Order.id','id','integer','required','one','{"integerWidth":{"bits":64,"signed":true}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (13,3,'Order.placedAt','placedAt','timestamp','required','one',NULL,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (14,3,'Order.status','status','string','required','one','{"length":{"max":20,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (15,3,'Order.channel','channel','string','absent-allowed','one','{"length":{"max":20,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (16,3,'Order.total','total','decimal','required','one','{"precision":14,"scale":2}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (17,4,'OrderLine.id','id','integer','required','one','{"integerWidth":{"bits":64,"signed":true}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (18,4,'OrderLine.lineNo','lineNo','integer','required','one','{"integerWidth":{"bits":16,"signed":true}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (19,4,'OrderLine.quantity','quantity','integer','required','one','{"integerWidth":{"bits":32,"signed":true}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (20,4,'OrderLine.unitPrice','unitPrice','decimal','required','one','{"precision":12,"scale":2}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (21,4,'OrderLine.lineTotal','lineTotal','decimal','required','one','{"precision":14,"scale":2}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (22,5,'Product.id','id','integer','required','one','{"integerWidth":{"bits":64,"signed":true}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (23,5,'Product.sku','sku','string','required','one','{"length":{"max":32,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (24,5,'Product.name','name','string','required','one','{"length":{"max":200,"unit":"unicode-scalar"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (25,5,'Product.price','price','decimal','required','one','{"precision":12,"scale":2}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (26,5,'Product.image','image','binary','absent-allowed','one','{"length":{"max":65536,"unit":"byte"}}'::jsonb,NULL,0) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;
INSERT INTO c.key_def VALUES (1,'identity',ARRAY[1],true) ON CONFLICT DO NOTHING;
INSERT INTO c.key_def VALUES (1,'account-code',ARRAY[2],false) ON CONFLICT DO NOTHING;
INSERT INTO c.key_def VALUES (3,'identity',ARRAY[12],true) ON CONFLICT DO NOTHING;
INSERT INTO c.key_def VALUES (4,'identity',ARRAY[17],true) ON CONFLICT DO NOTHING;
INSERT INTO c.key_def VALUES (5,'identity',ARRAY[22],true) ON CONFLICT DO NOTHING;
INSERT INTO c.rel_def VALUES (1,'sales','Customer.address','address',1,1,0,1,'owned',true,NULL,true,0,NULL) ON CONFLICT (rel_type_id) DO UPDATE SET source_min=EXCLUDED.source_min,source_max=EXCLUDED.source_max,target_min=EXCLUDED.target_min,target_max=EXCLUDED.target_max;
INSERT INTO c.rel_endpoint VALUES (1,1,2) ON CONFLICT DO NOTHING;
INSERT INTO c.rel_def VALUES (2,'sales','order-customer','customer',0,NULL,1,1,'independent',true,'identity',false,0,'orders') ON CONFLICT (rel_type_id) DO UPDATE SET source_min=EXCLUDED.source_min,source_max=EXCLUDED.source_max,target_min=EXCLUDED.target_min,target_max=EXCLUDED.target_max;
INSERT INTO c.rel_endpoint VALUES (2,3,1) ON CONFLICT DO NOTHING;
INSERT INTO c.rel_def VALUES (3,'sales','order-lines','lines',1,1,1,NULL,'owned',true,'identity',false,0,'order') ON CONFLICT (rel_type_id) DO UPDATE SET source_min=EXCLUDED.source_min,source_max=EXCLUDED.source_max,target_min=EXCLUDED.target_min,target_max=EXCLUDED.target_max;
INSERT INTO c.rel_endpoint VALUES (3,3,4) ON CONFLICT DO NOTHING;
INSERT INTO c.rel_def VALUES (4,'sales','line-product','product',0,NULL,1,1,'independent',true,'identity',false,0,'orderLines') ON CONFLICT (rel_type_id) DO UPDATE SET source_min=EXCLUDED.source_min,source_max=EXCLUDED.source_max,target_min=EXCLUDED.target_min,target_max=EXCLUDED.target_max;
INSERT INTO c.rel_endpoint VALUES (4,4,5) ON CONFLICT DO NOTHING;
