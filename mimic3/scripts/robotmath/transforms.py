#!usr/bin/env python
"""
Basic transforms for vectors, quaternions, and euler angles.
"""

import math


def quaternion_conjugate(q):
    """
    Computes quaternion conjugate
    :param q: Quaternion
    :return:
    """
    return [q[0], -q[1], -q[2], -q[3]]


def quaternion_multiply(q, r):
    """
    Computes quaternion multiplication
    :param q: Quaternion
    :param r: Quaternion
    :return:
    """
    q_w = q[0]
    q_x = q[1]
    q_y = q[2]
    q_z = q[3]
    r_w = r[0]
    r_x = r[1]
    r_y = r[2]
    r_z = r[3]
    return [
        q_w * r_w - q_x * r_x - q_y * r_y - q_z * r_z,
        q_w * r_x + q_x * r_w + q_y * r_z - q_z * r_y,
        q_w * r_y + q_y * r_w + q_z * r_x - q_x * r_z,
        q_w * r_z + q_z * r_w + q_x * r_y - q_y * r_x
    ]


def quaternion_vector_multiply(q, v):
    """
    Computes quaternion vector multiplication
    :param q: Quaternion
    :param v: Vector
    :return:
    """
    r = [0, v[0], v[1], v[2]]
    qm = quaternion_multiply(quaternion_multiply(q, r), quaternion_conjugate(q))
    return qm[1:]  # vector only


def quaternion_to_vectors(q):
    """
    Computes quaternion as vectors
    :param q: Quaternion
    :return:
    """
    x = [1, 0, 0]  # base vector
    y = [0, 1, 0]  # base vector
    z = [0, 0, 1]  # base vector
    return [
        quaternion_vector_multiply(q, x),
        quaternion_vector_multiply(q, y),
        quaternion_vector_multiply(q, z)
    ]


def quaternion_by_vectors(x, y, z):
    """
    Computes quaternion from vectors
    :param x: Vector
    :param y: Vector
    :param z: Vector
    :return: 
    """
    x_x = x[0]
    x_y = x[1]
    x_z = x[2]
    y_x = y[0]
    y_y = y[1]
    y_z = y[2]
    z_x = z[0]
    z_y = z[1]
    z_z = z[2]

    if x_x + y_y + z_z + 1 > 0.00001:
        s = math.sqrt(x_x + y_y + z_z + 1) * 2
        q1 = s / 4
        q2 = (-z_y + y_z) / s
        q3 = (-x_z + z_x) / s
        q4 = (-y_x + x_y) / s

    elif x_x > y_y and x_x > z_z:
        s = math.sqrt(x_x - y_y - z_z + 1) * 2
        q1 = (z_y - y_z) / s
        q2 = s / 4
        q3 = (y_x + x_y) / s
        q4 = (x_z + z_x) / s

    elif y_y > z_z:
        s = math.sqrt(-x_x + y_y - z_z + 1) * 2
        q1 = (x_z - z_x) / s
        q2 = (y_x + x_y) / s
        q3 = s / 4
        q4 = (z_y + y_z) / s

    else:
        s = math.sqrt(-x_x - y_y + z_z + 1) * 2
        q1 = (y_x - x_y) / s
        q2 = (x_z + z_x) / s
        q3 = (z_y + y_z) / s
        q4 = s / 4

    return [q1, q2, q3, q4]


def matrix_by_euler_angles(a, b, c):
    """
    Computes a matrix from Euler angles
    :param a: Rotation X
    :param b: Rotation Y
    :param c: Rotation Z
    :return:
    """
    _a = a * math.pi / -180
    _b = b * math.pi / -180
    _c = c * math.pi / -180
    ca = math.cos(_a)
    sa = math.sin(_a)
    cb = math.cos(_b)
    sb = math.sin(_b)
    cc = math.cos(_c)
    sc = math.sin(_c)
    x = [
        ca * cb,
        sa * cc + ca * sb * sc,
        sa * sc - ca * sb * cc
    ]
    y = [
        -sa * cb,
        ca * cc - sa * sb * sc,
        ca * sc + sa * sb * cc
    ]
    z = [
        sb,
        -cb * sc,
        cb * cc
    ]
    return [x, y, z]


def euler_angles_by_matrix(m):
    """
    Computes Euler angles from a rotation matrix.
    :param m:
    :return:
    """
    sb = m[2][0]
    if 1 - sb * sb < 0:
        cb = 0
    else:
        cb = math.sqrt(1 - sb * sb)
    ca = m[0][0]
    sa = -m[1][0]
    cc = m[2][2]
    sc = -m[2][1]
    if abs(m[0][0]) < 1E-7 and abs(m[1][0]) < 1E-7:
        cc = m[1][1]
        sc = m[1][2]
    _a = math.atan2(sa, ca)
    _b = math.atan2(sb, cb)
    _c = math.atan2(sc, cc)
    a = _a * -180 / math.pi
    b = _b * -180 / math.pi
    c = _c * -180 / math.pi
    return a, b, c


def vector_normalize(v):
    """
    Computes normalized vector
    :param v: Vector
    :return:
    """
    d = 0
    r = list(range(len(v)))
    for i in r:
        d += math.pow(v[i], 2)
    d = math.sqrt(d)
    for i in r:
        v[i] /= d
    return v


def vector_inverse(v):
    """
    Computes inverse vector
    :param v: Vector
    :return:
    """
    return [-n for n in v]
