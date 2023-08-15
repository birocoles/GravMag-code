import numpy as np
from scipy.spatial import distance
import warnings
from . import inverse_distance as idist
from . import check, utils, constants, convolve


# def kernel_grav(data_points, source_points, fields=["z"], check_input=True):
#     """
#     Compute the kernel matrix produced by a planar layer of monopoles.

#     parameters
#     ----------
#     data_points: dictionary
#         Dictionary containing the x, y and z coordinates at the keys 'x', 'y' and 'z',
#         respectively. Each key is a numpy array 1d having the same number of elements.
#     source_points: dictionary
#         Dictionary containing the x, y and z coordinates at the keys 'x', 'y' and 'z',
#         respectively. Each key is a numpy array 1d having the same number of elements.
#     field : list of strings
#         Defines the fields produced by the layer. The available options are:
#         "potential", "x", "y", "z", "xx", "xy", "xz", "yy", "yz", "zz".
#     check_input : boolean
#         If True, verify if the input is valid. Default is True.

#     returns
#     -------
#     G: list of numpy array 2d
#         List of N x M matrices defined by the kernels of the equivalent layer integral.
#     """

#     if check_input is True:
#         check.are_coordinates(data_points)
#         check.are_coordinates(source_points)
#         if np.max(data_points['z']) >= np.min(source_points['z']):
#             warnings.warn("verify if the surface containing data cross the equivalent layer")
#         # check if field is valid
#         for field in fields:
#             if field not in [
#                 "potential",
#                 "x",
#                 "y",
#                 "z",
#                 "xx",
#                 "xy",
#                 "xz",
#                 "yy",
#                 "yz",
#                 "zz",
#             ]:
#                 raise ValueError("invalid field {}".format(field))

#     # compute Squared Euclidean Distance Matrix (SEDM)
#     R2 = idist.sedm(data_points, source_points, check_input=False)

#     # compute the kernel matrices according to "fields"
#     G = []
#     for field in fields:
#         if field == "potential":
#             G.append(1.0 / np.sqrt(R2))
#         elif field in ["x", "y", "z"]:
#             G.append(idist.grad(data_points, source_points, R2, [field], False)[0])
#         else:  # field is in ["xx", "xy", "xz", "yy", "yz", "zz"]
#             G.append(idist.grad_tensor(data_points, source_points, R2, [field], False)[0])

#     return G


def kernel_matrix_dipoles(
    data_points,
    source_points,
    inc,
    dec,
    field="z",
    inct=None,
    dect=None,
    check_input=True,
):
    """
    Compute the kernel matrix produced by a planar layer of dipoles with
    constant magnetization direction.

    parameters
    ----------
    data_points: dictionary
        Dictionary containing the x, y and z coordinates at the keys 'x', 'y' and 'z',
        respectively. Each key is a numpy array 1d having the same number of elements.
    source_points: dictionary
        Dictionary containing the x, y and z coordinates at the keys 'x', 'y' and 'z',
        respectively. Each key is a numpy array 1d having the same number of elements.
    inc, dec : ints or floats
        Scalars defining the constant inclination and declination of the
        dipoles magnetization.
    field : string
        Defines the field produced by the layer. The available options are:
            - "potential" : magnetic scalar potential
            - "x", "y", "z" : Cartesian components of the magnetic induction
            - "t" : Component of magnetic induction along a constant direction
                with inclination and declination defined by "inct" and "dect",
                respectively. It approximates the total-field anomaly when
                "inct" and "dect" define the constant inclination and
                declination of the main field at the study area.
    inct, dect : ints or floats
        Scalars defining the constant inclination and declination of the
        magnetic field component. They must be not None if "field" is "t".
        Otherwise, they are ignored.
    check_input : boolean
        If True, verify if the input is valid. Default is True.

    returns
    -------
    G: numpy array 2d
        N x M matrix defined by the kernel of the equivalent layer integral.
    """

    if check_input is True:
        check.are_coordinates(data_points)
        check.are_coordinates(source_points)
        if np.max(data_points["z"]) >= np.min(source_points["z"]):
            warnings.warn(
                "verify if the surface containing data cross the equivalent layer"
            )
        if type(inc) not in [float, int]:
            raise ValueError("inc must be a scalar")
        if type(dec) not in [float, int]:
            raise ValueError("dec must be a scalar")
        # check if field is valid
        if field not in ["potential", "x", "y", "z", "t"]:
            raise ValueError("invalid field {}".format(field))
        if field == "t":
            if type(inct) not in [float, int]:
                raise ValueError("inct must be a scalar because field is 't'")
            if type(dect) not in [float, int]:
                raise ValueError("dect must be a scalar because field is 't'")

    # compute Squared Euclidean Distance Matrix (SEDM)
    R2 = idist.sedm(data_points, source_points, check_input=False)
    # compute the unit vector defined by inc and dec
    u = utils.unit_vector(inc, dec, check_input=False)

    # compute the kernel matrix according to "field"
    if field == "potential":
        Gx, Gy, Gz = idist.grad(
            data_points=data_points,
            source_points=source_points,
            SEDM=R2,
            components=["x", "y", "z"],
            check_input=False,
        )
        G = -(u[0] * Gx + u[1] * Gy + u[2] * Gz)
    elif field == "x":
        Gxx, Gxy, Gxz = idist.grad_tensor(
            data_points=data_points,
            source_points=source_points,
            SEDM=R2,
            components=["xx", "xy", "xz"],
            check_input=False,
        )
        G = u[0] * Gxx + u[1] * Gxy + u[2] * Gxz
    elif field == "y":
        Gxy, Gyy, Gyz = idist.grad_tensor(
            data_points=data_points,
            source_points=source_points,
            SEDM=R2,
            components=["xy", "yy", "yz"],
            check_input=False,
        )
        G = u[0] * Gxy + u[1] * Gyy + u[2] * Gyz
    elif field == "z":
        Gxz, Gyz, Gzz = idist.grad_tensor(
            data_points=data_points,
            source_points=source_points,
            SEDM=R2,
            components=["xz", "yz", "zz"],
            check_input=False,
        )
        G = u[0] * Gxz + u[1] * Gyz + u[2] * Gzz
    else:  # field is "t"
        # compute the unit vector defined by inct and dect
        t = utils.unit_vector(inct, dect, check_input=False)
        Gxx, Gxy, Gxz, Gyy, Gyz = idist.grad_tensor(
            data_points=data_points,
            source_points=source_points,
            SEDM=R2,
            components=["xx", "xy", "xz", "yy", "yz"],
            check_input=False,
        )
        axx = u[0] * t[0] - u[2] * t[2]
        axy = u[0] * t[1] + u[1] * t[0]
        axz = u[0] * t[2] + u[2] * t[0]
        ayy = u[1] * t[1] - u[2] * t[2]
        ayz = u[1] * t[2] + u[2] * t[1]
        G = axx * Gxx + axy * Gxy + axz * Gxz + ayy * Gyy + ayz * Gyz

    return G


def method_CGLS(
    sensibility_matrices, data_vectors, epsilon, ITMAX=50, check_input=True
):
    """
    Solves the unconstrained overdetermined problem to estimate the physical-property
    distribution on the equivalent layer via conjugate gradient normal equation residual
    (CGNR) (Golub and Van Loan, 2013, sec. 11.3) or conjugate gradient least squares (CGLS)
    (Aster et al., 2019, p. 165) method.

    parameters
    ----------
    sensibility_matrices: list of numpy arrays 2d
        List of matrices with same number of columns defining the kernel of the equivalent layer integral.
    data_vectors : list of numpy arrays 1d
        List of potential-field data.
    epsilon : float
        Tolerance for evaluating convergence criterion.
    ITMAX : int
        Maximum number of iterations. Default is 50.
    check_input : boolean
        If True, verify if the input is valid. Default is True.

    returns
    -------
    deltas : list of floats
        List of ratios of Euclidean norm of the residuals and number of data.
    parameters : numpy array 1d
        Physical property distribution on the equivalent layer.
    """

    if check_input == True:
        # check if G and data are consistent numpy arrays
        if type(sensibility_matrices) != list:
            raise ValueError("sensibility_matrices must be a list")
        if type(data_vectors) != list:
            raise ValueError("data_vectors must be a list")
        if len(sensibility_matrices) != len(data_vectors):
            raise ValueError(
                "sensibility_matrices and data_vectors must have the same number of elements"
            )
        for G, data in zip(sensibility_matrices, data_vectors):
            check.sensibility_matrix_and_data(matrix=G, data=data)
        # check if epsilon is a positive scalar
        check.is_scalar(x=epsilon, positive=True)
        # check if ITMAX is a positive integer
        check.is_integer(x=ITMAX, positive=True)

    # get number of data for each dataset and initialize residuals list
    ndatasets = len(data_vectors)
    ndata_per_dataset = []
    residuals = []
    for data in data_vectors:
        ndata_per_dataset.append(data.size)
        residuals.append(np.copy(data))
    ndata = np.sum(ndata_per_dataset)

    # compute the first delta and initialize the deltas list
    deltas = []
    delta = 0.0
    for res in residuals:
        delta += np.sum(res * res)
    delta = np.sqrt(delta) / ndata
    deltas.append(delta)

    # initialize the parameter vector
    parameters = np.zeros(ndata_per_dataset, dtype=float)

    # initialize auxiliary variables
    vartheta = np.zeros_like(parameters)
    for G, res in zip(sensibility_matrices, residuals):
        vartheta[:] += G.T @ res
    rho0 = np.sum(vartheta * vartheta)
    tau = 0.0
    eta = np.zeros_like(parameters)
    nus = []
    for i in range(ndatasets):
        nus.append(np.zeros_like(parameters))
    m = 1

    # updates
    while (delta > epsilon) and (m < ITMAX):
        eta[:] = vartheta + tau * eta
        aux = 0.0
        for G, nu in zip(sensibility_matrices, nus):
            nu[:] = G @ eta
            aux += np.sum(nu * nu)
        upsilon = rho0 / aux
        parameters[:] += upsilon * eta
        delta = 0.0
        for res, nu in zip(residuals, nus):
            res[:] -= upsilon * nu
            delta += np.sum(res * res)
        delta = np.sqrt(delta) / ndata
        deltas.append(delta)
        vartheta[:] = 0.0  # remember that vartheta in an array like parameters
        for sensibility_matrix, res in zip(sensibility_matrices, residuals):
            vartheta[:] += sensibility_matrix.T @ res
        rho = np.sum(vartheta * vartheta)
        tau = rho / rho0
        rho0 = rho
        m += 1

    return deltas, parameters


def method_column_action_C92(
    G, data, data_points, zlayer, epsilon, ITMAX, check_input=True
):
    """
    Estimates the physical-property distribution on the equivalent layer via column-action approach proposed by Cordell (1992).

    parameters
    ----------
    G: numpy array 2d
        N x M matrix defined by the kernel of the equivalent layer integral.
    data : numpy array 1d
        Potential-field data.
    data_points: dictionary
        Dictionary containing the x, y and z coordinates at the keys 'x', 'y' and 'z',
        respectively. Each key is a numpy array 1d having the same number of elements.
    zlayer : float
        Constant defining the vertical position for all equivalent sources.
    epsilon : float
        Tolerance for evaluating convergence criterion.
    ITMAX : int
        Maximum number of iterations. Default is 50.
    check_input : boolean
        If True, verify if the input is valid. Default is True.

    returns
    -------
    rmax_list : list of floats
        List of maximum absolute residuals.
    parameters : numpy array 1d
        Physical property distribution on the equivalent layer.
    """

    if check_input == True:
        # check if data and G are consistent numpy arrays
        check.sensibility_matrix_and_data(matrix=G, data=data)
        # check data points
        check.are_coordinates(coordinates=data_points)
        # check if zlayer result in a layer below the data points
        check.is_scalar(x=zlayer, positive=False)
        if np.any(zlayer <= data_points['z']):
            raise ValueError(
                "zlayer must be greater than the z coordinate of all data points"
            )
        # check if epsilon is a positive scalar
        check.is_scalar(x=epsilon, positive=True)
        # check if ITMAX is a positive integer
        check.is_integer(x=ITMAX, positive=True)

        # initializations
        data_aux = G@data
        scale = (data_aux@data)/(data_aux@data_aux)
        parameters = data * scale
        residuals = data - G@parameters
        imax = np.argmax(np.abs(residuals))
        rmax = residuals[imax]
        rmax_list = []
        rmax_list.append(abs(rmax))
        m = 1
        # updates
        while (abs(rmax) > epsilon) and (m < ITMAX):
            xmax = data_points['x'][imax]
            ymax = data_points['y'][imax]
            zmax = data_points['z'][imax]
            #dp = rmax * scale * np.abs(zlayer - zmax)
            dp = rmax * scale
            parameters[imax] += dp
            residuals[:] -= G[:, imax] * dp
            imax = np.argmax(np.abs(residuals))
            rmax = residuals[imax]
            rmax_list.append(abs(rmax))
            m += 1

        return rmax_list, parameters


def method_iterative_SOB17(
    G, data, epsilon, ITMAX=50, check_input=True
):
    """
    Solves the unconstrained problem to estimate the physical-property
    distribution on the equivalent layer via iterative method.

    parameters
    ----------
    G: numpy array 2d
        N x M matrix defined by the kernel of the equivalent layer integral.
    data : numpy array 1d
        Potential-field data.
    epsilon : float
        Tolerance for evaluating convergence criterion.
    ITMAX : int
        Maximum number of iterations. Default is 50.
    check_input : boolean
        If True, verify if the input is valid. Default is True.

    returns
    -------
    delta_list : list of floats
        List of ratios of Euclidean norm of the residuals and number of data.
    parameters : numpy array 1d
        Physical property distribution on the equivalent layer.
    """

    if check_input == True:
        # check if data and G are consistent numpy arrays
        check.sensibility_matrix_and_data(matrix=G, data=data)
        # check if epsilon is a positive scalar
        check.is_scalar(x=epsilon, positive=True)
        # check if ITMAX is a positive integer
        check.is_integer(x=ITMAX, positive=True)

    # initializations
    D = data.size
    data_aux = G@data
    scale = (data_aux@data)/(data_aux@data_aux)
    parameters = data * scale
    residuals = data - G@parameters
    delta_list = []
    delta = np.sqrt(np.sum(residuals * residuals)) / D
    delta_list.append(delta)
    nu = np.zeros_like(parameters)
    m = 1
    # updates
    while (delta > epsilon) and (m < ITMAX):
        dp = scale * residuals
        parameters[:] += dp
        nu[:] = G @ dp
        residuals[:] -= nu
        delta = np.sqrt(np.sum(residuals * residuals)) / D
        delta_list.append(delta)
        m += 1

    return delta_list, parameters


def method_iterative_deconvolution_TOB20(
    eigenvalues_matrices, Q, P, ordering, transposition_factors, data_vectors, epsilon, ITMAX=50, check_input=True
):
    """
    Solves the unconstrained overdetermined problem to estimate the physical-property
    distribution on the equivalent layer via convolutional equivalent-layer method
    proposed by Takahashi et al. (2020, 2022).

    parameters
    ----------
    eigenvalues_matrices : list of numpy arrays 2d
        List of matrices containing the eigenvalues of kernel matrices.
    Q: int
        Number of blocks along a column/row of the BTTB.
    P: int
        Number of rows/columns of each block forming the BTTB.
    ordering: string
        If "row", the eigenvalues are arranged along the rows of a matrix L;
        if "column", they are arranged along the columns of a matrix L.
    transposition_factors : list of ints
        List of ints defining the transposition factors of eigenvalues matrices.
    data_vectors : list of numpy arrays 1d
        List of potential-field data.
    epsilon : float
        Tolerance for evaluating convergence criterion.
    ITMAX : int
        Maximum number of iterations. Default is 50.
    check_input : boolean
        If True, verify if the input is valid. Default is True.

    returns
    -------
    deltas : list of floats
        List of ratios of Euclidean norm of the residuals and number of data.
    parameters : numpy array 1d
        Physical property distribution on the equivalent layer.
    """

    if check_input == True:
        if type(eigenvalues_matrices) != list:
            raise ValueError("eigenvalues_matrices must be a list")
        check.is_integer(x=Q, positive=True)
        check.is_integer(x=P, positive=True)
        if ordering not in ["row", "column"]:
            raise ValueError("invalid ordering")
        for L in eigenvalues_matrices:
            if ordering == "row":
                if L.shape != (2 * Q, 2 * P):
                    raise ValueError("L must have shape (2*Q, 2*P)")
            else: # if ordering == 'column':
                if L.shape != (2 * P, 2 * Q):
                    raise ValueError("L must have shape (2*P, 2*Q)")
        if type(transposition_factors) != list:
            raise ValueError("transposition_factors must be a list")
        for factor in transposition_factors:
            if (factor != 1) and (factor != -1):
                raise ValueError("transposition_factors must contain only 1 or -1 elements")
        if type(data_vectors) != list:
            raise ValueError("data_vectors must be a list")
        if len(eigenvalues_matrices) != len(data_vectors):
            raise ValueError(
                "eigenvalues_matrices and data_vectors must have the same number of elements"
            )
        if len(eigenvalues_matrices) != len(transposition_factors):
            raise ValueError(
                "eigenvalues_matrices and transposition_factors must have the same number of elements"
            )
        for data in data_vectors:
            check.is_array(x=data, ndim=1, shape=(Q*P,))
        # check if epsilon is a positive scalar
        check.is_scalar(x=epsilon, positive=True)
        # check if ITMAX is a positive integer
        check.is_integer(x=ITMAX, positive=True)

    ndatasets = len(data_vectors)
    ndata_per_dataset = Q*P
    ndata = ndatasets*ndata_per_dataset
    residuals = []
    for data in data_vectors:
        residuals.append(np.copy(data))

    # compute the first delta and initialize the deltas list
    deltas = []
    delta = 0.0
    for res in residuals:
        delta += np.sum(res * res)
    delta = np.sqrt(delta) / ndata
    deltas.append(delta)

    # initialize the parameter vector
    parameters = np.zeros(ndata_per_dataset, dtype=float)

    # initialize auxiliary variables
    vartheta = np.zeros_like(parameters)
    for L, res, factor in zip(eigenvalues_matrices, residuals, transposition_factors):
        vartheta[:] += convolve.product_BCCB_vector(
            L=factor*L, Q=Q, P=P, v=res, ordering=ordering, check_input=False
            )
    rho0 = np.sum(vartheta * vartheta)
    tau = 0.0
    eta = np.zeros_like(parameters)
    nus = []
    for i in range(ndatasets):
        nus.append(np.zeros_like(parameters))
    m = 1

    # updates
    while (delta > epsilon) and (m < ITMAX):
        eta[:] = vartheta + tau * eta
        aux = 0.0
        for L, nu in zip(eigenvalues_matrices, nus):
            nu[:] = convolve.product_BCCB_vector(L=L, Q=Q, P=P, v=eta, ordering=ordering, check_input=False)
            aux += np.sum(nu * nu)
        upsilon = rho0 / aux
        parameters[:] += upsilon * eta
        delta = 0.0
        for res, nu in zip(residuals, nus):
            res[:] -= upsilon * nu
            delta += np.sum(res * res)
        delta = np.sqrt(delta) / ndata
        deltas.append(delta)
        vartheta[:] = 0.0  # remember that vartheta in an array like parameters
        for L, res, factor in zip(eigenvalues_matrices, residuals, transposition_factors):
            vartheta[:] += convolve.product_BCCB_vector(
                L=factor*L, Q=Q, P=P, v=res, ordering=ordering, check_input=False
                )
        rho = np.sum(vartheta * vartheta)
        tau = rho / rho0
        rho0 = rho
        m += 1

    return deltas, parameters