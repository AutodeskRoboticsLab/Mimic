# Mimic

# Shelves

This directory contains the Mimic shelf `shelf_Mimic.mel`, an interface button
for using Mimic in Maya. It is written in MEL, a Maya programming language.


# Notes

- Modification of the Mimic shelf may cause Maya-version issues, especially for
  the purpose of backwards compatibility. If you still want to modify the shelf,
  right click and edit the shelf from within Maya.
  
- Known version issues:
  - If you open the shelf in a later version of Maya, it will apply a format to
    the shelf that may be incompatible with earlier versions of Maya.
  - Some flags, such as `backgroundColor 0 0 0` are not supported in earlier
    versions of Maya, such as 2016; try to avoid implementing these.


#
