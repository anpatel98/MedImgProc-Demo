"""
Author: qiuchang
Description: This script defines functions to process geometric and signal data for inverse solutions
"""
import numpy as np
import matplotlib.pyplot as plt
import copy
from scipy.special import expit
from scipy.signal import find_peaks
from scipy.spatial import ConvexHull

def generate_source_points(InnerGeometry, OuterGeometry, Config, output_file_source, plot=True):
    """
    Generates virtual source points for inner and outer geometries based on the deflation and inflation ratios
    specified in the Config. Optionally, it can plot the source points.
    """
    outerPoints = OuterGeometry['pts']
    innerPoints = InnerGeometry['pts']
    innerFaces = InnerGeometry['tri']

    Config['nInnerFaces'] = innerFaces.shape[0]

    # Calculate the center of the inner geometry points
    centerOfInner = np.mean(innerPoints, axis=0)

    # Generate virtual source points for the inner geometry
    innerSource = centerOfInner + Config['deflationRatio'] * (innerPoints - centerOfInner)

    # Generate virtual source points for the outer geometry
    outerSource = centerOfInner + Config['inflationRatio'] * (outerPoints - centerOfInner)

    # Combine inner and outer virtual source points
    sourcePts = np.vstack((innerSource, outerSource))
    if plot:
        plotsourcePts(innerPoints, outerPoints, sourcePts, output_file_source)

    return sourcePts


def plotsourcePts(innerPoints, outerPoints, sourcePts, save_path):
    """
    Plots a 3D scatter plot and saves it to a file.

    Parameters:
    sourcePts (numpy.ndarray): Array of 3D points, where the first set of rows represent inner source points,
                               and the remaining rows represent outer source points.
    save_path (str): Path to save the plot.
    """
    # First set of points
    x1, y1, z1 = sourcePts[:innerPoints.shape[0], 0], sourcePts[:innerPoints.shape[0], 1], sourcePts[:innerPoints.shape[0], 2]

    # Second set of points
    x2, y2, z2 = sourcePts[innerPoints.shape[0]:, 0], sourcePts[innerPoints.shape[0]:, 1], sourcePts[innerPoints.shape[0]:, 2]

    x3, y3, z3 = innerPoints[:, 0], innerPoints[:, 1], innerPoints[:, 2]
    x4, y4, z4 = outerPoints[:, 0], outerPoints[:, 1], outerPoints[:, 2]

    # Create a 3D plot
    fig = plt.figure(figsize=(12, 6))
    ax1 = fig.add_subplot(121, projection='3d')
    ax1.scatter(x1, y1, z1, c='r', label='source cortex')
    ax1.scatter(x2, y2, z2, c='b', label='source skull')
    ax1.set_xlabel('X Label')
    ax1.set_ylabel('Y Label')
    ax1.set_zlabel('Z Label')
    ax1.legend()
    ax1.set_title('sourcePts')

    ax2 = fig.add_subplot(122, projection='3d')
    ax2.scatter(x3, y3, z3, c='g', label='cortex')
    ax2.scatter(x4, y4, z4, c='y', label='skull')
    ax2.set_xlabel('X Label')
    ax2.set_ylabel('Y Label')
    ax2.set_zlabel('Z Label')
    ax2.legend()
    ax2.set_title('Inner and Outer Points')

    plt.savefig(save_path)
    plt.close()


def generate_a_matrix(sourcePts, Geometry, skullPotential, *args):
    """
    Generates an A-matrix for forward or inverse boundary conditions based on the input arguments.

    Parameters:
    sourcePts : Source points
    Geometry : Geometry dictionary containing points and triangles
    skullPotential : Potential values on the skull boundary
    *args : Variable arguments to specify forward/inverse matrix computation

    Returns:
    A : Generated A-matrix
    bound : Boundary conditions for the A-matrix
    """
    if len(args) == 0:
        raise ValueError("Less than minimal input arguments. Please provide additional input arguments!")

    elif len(args) == 1:
        if args[0] == 'forward':
            bndPts = Geometry['cortex']['pts']
            A = compute_dirichlet_boundary(sourcePts, bndPts)
            bound = None

        elif args[0] == 'inverse':
            skullPts = Geometry['skull']['pts']
            skullTri = Geometry['skull']['tri']
            dMatrix = compute_dirichlet_boundary(sourcePts, skullPts)
            nMatrix = compute_neumann_boundary(sourcePts, dMatrix, skullPts, skullTri)
            A = compute_complete_boundary(dMatrix, nMatrix)
            skullCurrent = np.zeros((nMatrix.shape[0], skullPotential.shape[1]))
            bound = np.vstack((skullPotential, skullCurrent))

        else:
            raise ValueError("Invalid A-matrix computing option!")

    elif len(args) == 2:
        if args[0].lower() == 'inverse':
            skullPts = Geometry['skull']['pts']
            dMatrix = compute_dirichlet_boundary(sourcePts, skullPts)

            if args[1] == 'same':
                currentBndPts = skullPts
                currentBndTri = Geometry['skull']['tri']

            elif args[1] == 'full':
                currentBndPts = Geometry['skull']['pts']
                currentBndTri = Geometry['skull']['tri']

            else:
                raise ValueError("Invalid inverse computing option!")

            rMatrix = compute_dirichlet_boundary(sourcePts, currentBndPts)
            nMatrix = compute_neumann_boundary(sourcePts, rMatrix, currentBndPts, currentBndTri)
            A = compute_complete_boundary(dMatrix, nMatrix)
            skullCurrent = np.zeros((nMatrix.shape[0], skullPotential.shape[1]))
            bound = np.vstack((skullPotential, skullCurrent))

        else:
            raise ValueError(
                "Your first input argument is NOT inverse computation! Only inverse computation needs two arguments!")

    else:
        raise ValueError("Too many input arguments. Please check input arguments!")

    return A, bound


def compute_dirichlet_boundary(sourcePts, bndPts):
    """
    Computes the Dirichlet boundary matrix between source and boundary points.

    Parameters:
    sourcePts : Source points
    bndPts : Boundary points

    Returns:
    dMatrix : Dirichlet boundary matrix
    """
    sourceNum = sourcePts.shape[0]
    bndNum = bndPts.shape[0]
    A1 = np.sum(bndPts ** 2, axis=1).reshape(-1, 1) * np.ones((1, sourceNum))
    A2 = np.sum(sourcePts ** 2, axis=1) * np.ones((bndNum, 1))
    A3 = -2 * np.dot(bndPts, sourcePts.T)
    dMatrix = 1.0 / np.sqrt(A1 + A2 + A3)
    return dMatrix

def compute_normal(vertex, face):
    nface = face.shape[0]
    nvert = np.max(face) + 1  # 注意：Python 中的索引从 0 开始
    normal = np.zeros((nvert, 3))
    facev = np.zeros((nface, 3))

    for i in range(nface):
        f = face[i, :]
        n = np.cross(vertex[f[2], :] - vertex[f[0], :], vertex[f[1], :] - vertex[f[0], :])
        n = n / np.linalg.norm(n)
        facev[i, :] = n
        for j in range(3):
            normal[f[j], :] += n

    # normalize
    for i in range(nvert):
        n = normal[i, :]
        normal[i, :] = n / np.linalg.norm(n)

    return normal
def compute_neumann_boundary(sourcePts, dMatrix, bndPts, bndTri):
    """
    Computes the Neumann boundary matrix between source and boundary points based on the normal vectors.

    Parameters:
    sourcePts : Source points
    dMatrix : Dirichlet boundary matrix
    bndPts : Boundary points
    bndTri : Boundary triangles defining the mesh

    Returns:
    nMatrix : Neumann boundary matrix
    """
    sourceNum = sourcePts.shape[0]
    skullNormal = compute_normal(bndPts, bndTri)
    sub1 = np.dot(skullNormal, sourcePts.T)
    sub2 = np.sum(bndPts * skullNormal, axis=1).reshape(-1, 1) * np.ones((1, sourceNum))
    nMatrix = (sub1 - sub2) * dMatrix ** 3
    return nMatrix


def compute_complete_boundary(dMatrix, nMatrix):
    """
    Combines the Dirichlet and Neumann boundary matrices into a complete boundary matrix, adding
    constraint rows to distinguish Dirichlet and Neumann conditions.

    Parameters:
    dMatrix : Dirichlet boundary matrix
    nMatrix : Neumann boundary matrix

    Returns:
    completeMatrix : Complete boundary matrix with constraints
    """
    completeMatrix = np.vstack((dMatrix, nMatrix))
    dconsBnd = np.ones((dMatrix.shape[0], 1))  # Constraint for Dirichlet boundary
    nconsBnd = np.zeros((nMatrix.shape[0], 1))  # Constraint for Neumann boundary
    consBnd = np.vstack((dconsBnd, nconsBnd))
    completeMatrix = np.hstack((consBnd, completeMatrix))
    return completeMatrix


def rescale_geometry(Geometry, scalefactor, goodCh):
    """
    Rescale the parameters in the Geometry dictionary by the given scalefactor.
    """
    Geometry_ = copy.deepcopy(Geometry)
    rawskullPts = Geometry_['skull']['pts']

    if len(goodCh) != rawskullPts.shape[0]:
        skullTri, skullX, skullY, skullZ = meshpts(
            rawskullPts[goodCh, 0], rawskullPts[goodCh, 1], rawskullPts[goodCh, 2], plot=False)
        skullPts = np.column_stack((skullX, skullY, skullZ))
    else:
        skullPts = Geometry_['skull']['pts']
        skullTri = Geometry_['skull']['tri']


    Geometry_['skull']['pts'] = skullPts * scalefactor
    Geometry_['skull']['tri'] = skullTri
    Geometry_['cortex']['pts'] = Geometry_['cortex']['pts'] * scalefactor

    return Geometry_


def calculate_weight(edge_vector, cf_vector):
    """
    Calculates the weight for an edge vector based on its cosine similarity to the cf_vector.
    """
    dot_product = np.dot(edge_vector, cf_vector)
    norm_cf = np.linalg.norm(cf_vector)
    norm_edge = np.linalg.norm(edge_vector)
    cos_theta = dot_product / (norm_edge * norm_cf)
    weight = 1 - (cos_theta) ** 2
    return weight


def apply_weights_to_edges(edge_vectors, cf_vector):
    """
    Applies calculated weights to a list of edge vectors based on their orientation relative to cf_vector.
    """
    weights = [calculate_weight(edge_vector, cf_vector) for edge_vector in edge_vectors]
    return np.array(weights)


def generate_edge_matrix(triangles, points):
    """
    Generates an edge matrix based on triangles and applies weights based on orientation.
    """
    centroid = np.mean(points, axis=0)
    normalized_points = points - centroid
    cov_matrix = np.cov(normalized_points, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    principal_axis = eigenvectors[:, np.argmax(eigenvalues)]
    cf_vector = principal_axis

    edges = []
    for tri in triangles:
        edges.append([tri[0], tri[1]])  # Edge 1: point 0 -> point 1
        edges.append([tri[1], tri[2]])  # Edge 2: point 1 -> point 2
        edges.append([tri[2], tri[0]])  # Edge 3: point 2 -> point 0

    edges = np.array(edges)
    n_edges = edges.shape[0]
    edge_vectors = np.zeros((n_edges, points.shape[1]))
    edge_matrix = np.zeros((n_edges, points.shape[0]))

    for i, (start, end) in enumerate(edges):
        edge_matrix[i, start] = 1  # Start point of the edge
        edge_matrix[i, end] = -1  # End point of the edge
        edge_vectors[i] = points[end] - points[start]

    weights = apply_weights_to_edges(edge_vectors, cf_vector)
    weights_scale = expit((weights - 0.5) * 40)
    weight_edge_matrix = edge_matrix * weights_scale[:, np.newaxis]

    return weight_edge_matrix, edge_matrix

def MFS_inverse(G,remaining_channels,sig_inverse,Config,output_file_source,constrain='e'):
    GRescale = rescale_geometry(G, Config['scaleFactor'], remaining_channels)
    sourcePts = generate_source_points(GRescale['cortex'], GRescale['skull'], Config,output_file_source)
    mfsInvA, bound = generate_a_matrix(sourcePts, GRescale, sig_inverse, 'inverse', 'same')
    fwdA,_= generate_a_matrix(sourcePts, GRescale, None, 'forward')

    bad_chs = np.sum(np.abs(sig_inverse), axis=1) == 0
    bad_ch_bound = np.repeat(bad_chs[:, np.newaxis], 2, axis=1).flatten()
    if bad_ch_bound.any():
        bound = bound[~bad_ch_bound]
        mfsInvA = mfsInvA[~bad_ch_bound]

    if constrain=='we':
        betaW, betaE = generate_edge_matrix(G['cortex']['tri'], G['cortex']['pts'])
        nTimeFrames = sig_inverse.shape[1]

        num_add = mfsInvA.shape[1] - 1 - betaW.shape[1]
        beta_extend = np.hstack(
            [np.zeros((betaW.shape[0], 1)), Config['gamma'] * betaW, np.zeros((betaW.shape[0], num_add))])
        tmpInvA = np.vstack([mfsInvA, beta_extend])
        bound_beta = np.vstack([bound, np.zeros((betaW.shape[0], nTimeFrames))])


    elif constrain == 'e':
        betaW, betaE = generate_edge_matrix(G['cortex']['tri'], G['cortex']['pts'])
        nTimeFrames = sig_inverse.shape[1]

        num_add = mfsInvA.shape[1] - 1 - betaE.shape[1]
        beta_extend = np.hstack(
            [np.zeros((betaE.shape[0], 1)), Config['gamma'] * betaE, np.zeros((betaE.shape[0], num_add))])
        tmpInvA = np.vstack([mfsInvA, beta_extend])
        bound_beta = np.vstack([bound, np.zeros((betaE.shape[0], nTimeFrames))])

    else:
        tmpInvA = mfsInvA
        bound_beta = bound

    column_norms = np.linalg.norm(mfsInvA, axis=0)
    column_norms[0] = 0
    min_val = np.min(column_norms)
    max_val = np.max(column_norms)

    # Normalize the data to 0-1
    normalized_data = (column_norms - min_val) / (max_val - min_val)
    normalized_data_power = np.power(normalized_data, Config['power'])

    dMatrix_reg_array = np.diag(normalized_data_power)

    x_reg = np.linalg.inv(tmpInvA.T @ tmpInvA + Config['lambda'] * dMatrix_reg_array) @ tmpInvA.T @ bound_beta

    cortex_mfs = fwdA @ x_reg[1:, :] + np.tile(x_reg[0, :], (fwdA.shape[0], 1))

    print('MFS inverse Finished')
    cortex_pp = calculate_p2p(cortex_mfs)

    return cortex_pp, cortex_mfs, x_reg, fwdA, mfsInvA, bound, tmpInvA

def make_animation_pots_file(filename, x, y, z, xcompd, mesh):
    nnodes = xcompd.shape[0]  # Number of nodes
    nframes = xcompd.shape[1]  # Number of frames
    nelements = len(mesh)  # Number of elements in the mesh

    # Debugging: Print sizes to ensure they match
    print(f'Number of nodes: {nnodes}')
    print(f'x length: {len(x)}, y length: {len(y)}, z length: {len(z)}')
    print(f'Number of frames: {nframes}')
    print(f'Number of elements: {nelements}')

    # Ensure that x, y, z have the correct number of nodes
    if len(x) != nnodes or len(y) != nnodes or len(z) != nnodes:
        raise ValueError("The length of x, y, and z must match the number of nodes in xcompd.")

    with open(filename, 'w') as fid1:
        # Write the header
        fid1.write('TITLE = "Epicardial Potentials"\n')
        fid1.write('VARIABLES = "X","Y","Z","Potential"\n')

        for i in range(1):
            # Write zone information for each frame
            numstring = f'ZONE T="{i + 1}", N={nnodes}, E={nelements}, F=FEPOINT, ET=TRIANGLE\n'
            fid1.write(numstring)

            # Write node data (x, y, z, potentials)
            for j in range(nnodes):
                fid1.write(f'{x[j]:f}\t{y[j]:f}\t{z[j]:f}\t{xcompd[j, i]:f}\n')

            # Write element data (mesh)
            for element in mesh:
                fid1.write(f'{element[0]}\t{element[1]}\t{element[2]}\n')

    print(f'File "{filename}" has been successfully created.')
def meshpts(x, y, z, plot=False):
    """
    Generates a mesh grid from x, y, z coordinates, centers the coordinates, and transforms them
    into spherical coordinates. Optionally, displays the mesh plot.
    """
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    z = z[~np.isnan(z)]
    center = np.mean(np.column_stack([x, y, z]), axis=0)
    x -= center[0]
    y -= center[1]
    z -= center[2]

    theta, phi, rho = cart2sph(x, y, z)
    new_x = np.cos(phi) * np.cos(theta)
    new_y = np.cos(phi) * np.sin(theta)
    new_z = np.sin(phi)
    tri = ConvexHull(np.column_stack([new_x, new_y, new_z])).simplices

    X = x + center[0]
    Y = y + center[1]
    Z = z + center[2]

    if plot:
        PlotMeshAndSphere(tri, new_x, new_y, new_z, X, Y, Z)

    return tri, X, Y, Z

def cart2sph(x, y, z):
    """
    Converts Cartesian coordinates (x, y, z) to spherical coordinates (theta, phi, rho).
    """
    hxy = np.hypot(x, y)
    rho = np.hypot(hxy, z)
    theta = np.arctan2(y, x)
    phi = np.arctan2(z, hxy)
    return theta, phi, rho


def PlotMeshAndSphere(tri, new_xx, new_yy, new_zz, interpx, interpy, interpz):
    """
    Plots the mesh and spherical surface using 3D plots for visual comparison.
    """
    fig = plt.figure(figsize=(10, 5))
    ax1 = fig.add_subplot(121, projection='3d')
    ax2 = fig.add_subplot(122, projection='3d')

    ax1.plot_trisurf(new_xx, new_yy, new_zz, triangles=tri, cmap='viridis')
    ax2.plot_trisurf(interpx, interpy, interpz, triangles=tri, cmap='viridis')


def calculate_p2p(signal):
    """Calculates the mean peak-to-peak amplitude for each channel in the signal."""
    p2p_amplitudes = np.zeros(signal.shape)

    for i in range(signal.shape[0]):
        # Identify positive and negative peaks
        ploc = find_peaks(signal[i, :])[0]
        nloc = find_peaks(-signal[i, :])[0]

        # Extract positive and negative peak values
        eeg_ppeaks = signal[i, ploc]
        eeg_npeaks = signal[i, nloc]

        # Calculate peak-to-peak amplitude
        if len(ploc) > len(nloc):
            pp = ((eeg_ppeaks[:-1] - eeg_npeaks) + (eeg_ppeaks[1:] - eeg_npeaks)) / 2
        elif len(ploc) < len(nloc):
            pp = ((-eeg_npeaks[:-1] + eeg_ppeaks) + (-eeg_npeaks[1:] + eeg_ppeaks)) / 2
        else:
            pp = eeg_ppeaks - eeg_npeaks

        # Store the mean P2P amplitude
        p2p_amplitudes[i, :] = np.mean(pp)

    return p2p_amplitudes

