# Testing PDX File Generation

Every time, we add new functionality to the library, we have to test that the library is able to parse the pdx file
as well as generate the schematically correct pdx file. The below commands will help generate the PDX file and 
validate against the ODX schema.

```bash
python3 examples/mksomersaultpdx.py examples/somersault.pdx
unzip examples/somersault.pdx somersault.odx-d
xmllint --schema schema/odx.xsd --noout somersault.odx-d
rm -rf somersault.odx-d
```

You should see the below output for a successful validation.

```bash
$ xmllint --schema schema/odx.xsd --noout somersault.odx-d
somersault.odx-d validates
```
 