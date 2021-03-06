from typing import Tuple
import numpy as np
from numpy import ndarray
from dataclasses import dataclass, field
from scipy.linalg import block_diag
import scipy.linalg as la
from utils import rotmat2d
from utils import wrapToPi
from JCBB import JCBB
import utils
import solution


@dataclass
class EKFSLAM:
    Q: ndarray
    R: ndarray
    do_asso: bool
    alphas: 'ndarray[2]' = field(default=np.array([0.001, 0.0001]))
    sensor_offset: 'ndarray[2]' = field(default=np.zeros(2))

    def f(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """Add the odometry u to the robot state x.

        Parameters
        ----------
        x : np.ndarray, shape=(3,)
            the robot state
        u : np.ndarray, shape=(3,)
            the odometry

        Returns
        -------
        np.ndarray, shape = (3,)
            the predicted state
        """
        uprev      = u[0]
        vprev      = u[1]
        phiprev    = wrapToPi(u[2])

        xprev      = x[0]
        yprev      = x[1]
        psiprev    = wrapToPi(x[2])      

        xpred = np.array([[xprev+uprev*np.cos(psiprev)-vprev*np.sin(psiprev)],
                        [yprev+uprev*np.sin(psiprev)+vprev*np.sin(psiprev)],
                        [phiprev+psiprev]])
        
        # TODO, eq (11.7). Should wrap heading angle between (-pi, pi), see utils.wrapToPi
        xpred.shape=(3,)
        return xpred

    def Fx(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """Calculate the Jacobian of f with respect to x.

        Parameters
        ----------
        x : np.ndarray, shape=(3,)
            the robot state
        u : np.ndarray, shape=(3,)
            the odometry

        Returns
        -------
        np.ndarray
            The Jacobian of f wrt. x.
        """
        # TODO replace this with your own code
        #Fx = solution.EKFSLAM.EKFSLAM.Fx(self, x, u)
        #return Fx
        uk      = u[0]
        vk      = u[1]
        phik    = u[2]

        xk     = x[0]
        yk     = x[1]
        psik   = x[2]

        Fx = np.eye(3)

        arg1 = -uk*np.sin(psik)-vk*np.cos(psik)
        arg2 = uk*np.cos(psik)-vk*np.sin(psik)

        Fx[0][2]=arg1
        Fx[1][2]=arg2

        return Fx

    def Fu(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """Calculate the Jacobian of f with respect to u.

        Parameters
        ----------
        x : np.ndarray, shape=(3,)
            the robot state
        u : np.ndarray, shape=(3,)
            the odometry

        Returns
        -------
        np.ndarray
            The Jacobian of f wrt. u.
        """
        # TODO replace this with your own code
        #Fu = solution.EKFSLAM.EKFSLAM.Fu(self, x, u)
        #return Fu
        uk      = u[0]
        vk      = u[1]
        phik    = u[2]

        xk     = x[0]
        yk     = x[1]
        psik   = x[2]

        Fu = np.zeros((3,3))
        Fu[0][0] = np.cos(psik)
        Fu[1][1] = np.cos(psik)
        Fu[2][2] = 1
        Fu[1][0] = np.sin(psik)
        Fu[0][1] = -1*np.sin(psik)

        return Fu

    def predict(
        self, eta: np.ndarray, P: np.ndarray, z_odo: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Predict the robot state using the zOdo as odometry the corresponding state&map covariance.

        Parameters
        ----------
        eta : np.ndarray, shape=(3 + 2*#landmarks,)
            the robot state and map concatenated
        P : np.ndarray, shape=(3 + 2*#landmarks,)*2
            the covariance of eta
        z_odo : np.ndarray, shape=(3,)
            the measured odometry

        Returns
        -------
        Tuple[np.ndarray, np.ndarray], shapes= (3 + 2*#landmarks,), (3 + 2*#landmarks,)*2
            predicted mean and covariance of eta.
        """

        #etapred, P = solution.EKFSLAM.EKFSLAM.predict(self, eta, P, z_odo)
        #return etapred, P

        # check inout matrix
        assert np.allclose(P, P.T), "EKFSLAM.predict: not symmetric P input"
        assert np.all(
            np.linalg.eigvals(P) >= 0
        ), "EKFSLAM.predict: non-positive eigen values in P input"
        assert (
            eta.shape * 2 == P.shape
        ), "EKFSLAM.predict: input eta and P shape do not match"
        etapred = np.empty_like(eta)

        x = eta[:3]
        etapred[:3] = self.f(x,z_odo)  # TODO robot state prediction
        etapred[3:] = eta[3:]  # TODO landmarks: no effect

        Fx = self.Fx(x, z_odo)
        Fu = self.Fu(x, z_odo)

        # evaluate covariance prediction in place to save computation
        # only robot state changes, so only rows and colums of robot state needs changing
        # cov matrix layout:
        # [[P_xx, P_xm],
        # [P_mx, P_mm]]
        P[:3, :3] = Fx@P[:3,:3]@Fx.T+ Fu@self.Q@Fu.T  # TODO robot cov prediction
        P[:3, 3:] = Fx@P[:3,3:]  # TODO robot-map covariance prediction
        P[3:, :3] = P[3:,:3]@Fx.T # TODO map-robot covariance: transpose of the above
        #print(np.linalg.eigvals(P))
        assert np.allclose(P, P.T), "EKFSLAM.predict: not symmetric P"
        assert np.all(
            np.linalg.eigvals(P) > 0
        ), "EKFSLAM.predict: non-positive eigen values"
        assert (
            etapred.shape * 2 == P.shape
        ), "EKFSLAM.predict: calculated shapes does not match"

        return etapred, P

    def h(self, eta: np.ndarray) -> np.ndarray:
        """Predict all the landmark positions in sensor frame.

        Parameters
        ----------
        eta : np.ndarray, shape=(3 + 2 * #landmarks,)
            The robot state and landmarks stacked.

        Returns
        -------
        np.ndarray, shape=(2 * #landmarks,)
            The landmarks in the sensor frame.
        """

        # TODO replace this with your own code
        #zpred = solution.EKFSLAM.EKFSLAM.h(self, eta)
        #return zpred

       # extract states and map
        x = eta[0:3]
        # reshape map (2, #landmarks), m[:, j] is the jth landmark
        m = eta[3:].reshape((-1, 2)).T

        Rot = rotmat2d(-x[2])

        # None as index ads an axis with size 1 at that position.
        # Numpy broadcasts size 1 dimensions to any size when needed
        n_landmarks = len(m[0,:])
        delta_m = np.zeros_like(m)
        for i in range(n_landmarks):
            delta_m[:,i] = m[:,i] - x[0:2]
            
        # delta_m = None  # TODO, relative position of landmark to sensor on robot in world frame

        # TODO, predicted measurements in cartesian coordinates, beware sensor offset for VP
        zpredcart = np.zeros_like(m)
        for i in range(n_landmarks):
            zpredcart[:,i] = Rot@delta_m[:,i] - self.sensor_offset
        # zpredcart = None

        zpred_r = np.zeros((n_landmarks,))
        zpred_theta = np.zeros((n_landmarks,))
        for i in range(n_landmarks):
            zpred_r[i] = np.linalg.norm(zpredcart[:,i],2)
            zpred_theta[i] = np.arctan2(zpredcart[1,i],zpredcart[0,i])
        # zpred_r = None  # TODO, ranges
        # zpred_theta = None  # TODO, bearings
        zpred = np.array([zpred_r,zpred_theta])  # TODO, the two arrays above stacked on top of each other vertically like
        # [ranges;
        #  bearings]
        # into shape (2, #lmrk)

        # stack measurements along one dimension, [range1 bearing1 range2 bearing2 ...]
        zpred = zpred.T.ravel()

        assert (
            zpred.ndim == 1 and zpred.shape[0] == eta.shape[0] - 3
        ), "SLAM.h: Wrong shape on zpred"

        return zpred

    def h_jac(self, eta: np.ndarray) -> np.ndarray:
        """Calculate the jacobian of h.
        Parameters
        ----------
        eta : np.ndarray, shape=(3 + 2 * #landmarks,)
            The robot state and landmarks stacked.
        Returns
        -------
        np.ndarray, shape=(2 * #landmarks, 3 + 2 * #landmarks)
            the jacobian of h wrt. eta.
        """
        # H_true = solution.EKFSLAM.EKFSLAM.h_jac(self, eta)
        # print(H)
        # return H

        # extract states and map
        x = eta[0:3]
        # reshape map (2, #landmarks), m[j] is the jth landmark
        m = eta[3:].reshape((-1, 2)).T

        numM = m.shape[1]

        Rot = rotmat2d(x[2])

        # TODO, relative position of landmark to robot in world frame. m - rho that appears in (11.15) and (11.16)
        # delta_m = None
        delta_m = np.zeros_like(m)
        for i in range(numM):
            delta_m[:,i] = m[:,i] - x[0:2]

        # TODO, (2, #measurements), each measured position in cartesian coordinates like
        zc = np.zeros_like(m)
        zpred_r = np.zeros((numM,))
        for i in range(numM):
            zc[:,i] = delta_m[:,i] - Rot@self.sensor_offset
            zpred_r[i] = np.linalg.norm(zc[:,i],2)

        # zc = None
        # [x coordinates;
        #  y coordinates]
            

        # zpred = None  # TODO (2, #measurements), predicted measurements, like
        # [ranges;
        #  bearings]

        Rpihalf = rotmat2d(np.pi / 2)

        # In what follows you can be clever and avoid making this for all the landmarks you _know_
        # you will not detect (the maximum range should be available from the data).
        # But keep it simple to begin with.

        # # Allocate H and set submatrices as memory views into H
        # # You may or may not want to do this like this
        # # TODO, see eq (11.15), (11.16), (11.17)
        H = np.zeros((2 * numM, 3 + 2 * numM))
        # Hx = H[:, :3]  # slice view, setting elements of Hx will set H as well
        # Hm = H[:, 3:]  # slice view, setting elements of Hm will set H as well



        # proposed way is to go through landmarks one by one
        # preallocate and update this for some speed gain if looping
        jac_z_cb = -np.eye(2, 3)
        Hx = np.zeros((2,3))
        Hm = np.zeros((2,2))
        for i in range(numM):  # But this whole loop can be vectorized
            indx = 2 * i  # starting postion of the ith landmark into H
            # the inds slice for the ith landmark into H
            indxs = slice(indx, indx + 2)

            indm = 3 + i*2
            indms = slice(indm, indm + 2)

            # TODO: Set H or Hx and Hm here
            jac_z_cb[:,2] = -Rpihalf@delta_m[:,i]


            Hx[0,0:3] =  zc[:,i].T/zpred_r[i]@jac_z_cb
            Hx[1,0:3] = zc[:,i].T@Rpihalf.T@jac_z_cb/zpred_r[i]**2

            Hm[0,0:2] = zc[:,i].T/zpred_r[i]
            Hm[1,0:2] = -zc[:,i].T@Rpihalf/zpred_r[i]**2
            
            H[indxs, 0:3] = Hx
            H[indxs, indms] = Hm


        # TODO: You can set some assertions here to make sure that some of the structure in H is correct
        # print("TRY:",H)
        # print("TRUE:",H_true)
        # print("H- H_true:", H- H_true)
        return H

    def add_landmarks(
        self, eta: np.ndarray, P: np.ndarray, z: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate new landmarks, their covariances and add them to the state.
        Parameters
        ----------
        eta : np.ndarray, shape=(3 + 2*#landmarks,)
            the robot state and map concatenated
        P : np.ndarray, shape=(3 + 2*#landmarks,)*2
            the covariance of eta
        z : np.ndarray, shape(2 * #newlandmarks,)
            A set of measurements to create landmarks for
        Returns
        -------
        Tuple[np.ndarray, np.ndarray], shapes=(3 + 2*(#landmarks + #newlandmarks,), (3 + 2*(#landmarks + #newlandmarks,)*2
            eta with new landmarks appended, and its covariance
        """
        # TODO replace this with your own code
        # etaadded_correct, Padded_correct = solution.EKFSLAM.EKFSLAM.add_landmarks(
        #    self, eta, P, z)

        n = P.shape[0]
        assert z.ndim == 1, "SLAM.add_landmarks: z must be a 1d array"

        numLmk = z.shape[0] // 2
        lmnew = np.empty_like(z)

        Gx = np.zeros((numLmk * 2, 3))
        #print("first print",Gx)
        Rall = np.zeros((numLmk * 2, numLmk * 2))
        # print(self.h(eta))
        # I2 = np.eye(2)  # Preallocate, used for Gx
        # For transforming landmark position into world frame
        sensor_offset_world = rotmat2d(eta[2]) @ self.sensor_offset
        sensor_offset_world_der = rotmat2d(
            eta[2] + np.pi / 2) @ self.sensor_offset  # Used in Gx

        for j in range(numLmk):
            ind = 2 * j
            inds = slice(ind, ind + 2)
            zj = z[inds]

            ## Measurement stuff
            zrj = zj[0]  #radius
            zphij= zj[1] #phi angle
            # print(zj)
            #eta stuff
            psi = eta[2] #psi/yaw angle

            rot = rotmat2d(zphij+psi)  # TODO, rotmat in Gz
            # TODO, calculate position of new landmark in world frame
            x_z = zrj*np.cos(zphij)
            y_z = zrj*np.sin(zphij)

            z_c = np.array([x_z,y_z])

            lmnew[inds] =np.array([eta[0],eta[1]]) + rotmat2d(psi)@z_c+sensor_offset_world
            ## Covariance robot state x
            Gx[inds, :2] = np.eye(2)  # TODO
            vec = np.array([-np.sin(zphij+psi),np.cos(zphij+psi)]).T
            Gx[inds, 2] =zrj*vec+sensor_offset_world_der.T
            

            # Covariance measured state z
            IGz = np.eye(2)
            IGz[1][1] = zrj
            Gz = rot @ IGz
            # TODO, Gz * R * Gz^T, transform measurement covariance from polar to cartesian coordinates
            # J = np.array([[np.cos(zphij),-zrj*np.sin(zphij)],
            #             [np.sin(zphij),zrj*np.cos(zphij)]])
            # Gz_c = J@Gz@J.T
            Gz_c = Gz@self.R@Gz.T

    
            Rall[inds, inds] = Gz_c
            
        #print("\n Rall",block_diag(Rall))
        #print(lmnew)
        assert len(lmnew) % 2 == 0, "SLAM.add_landmark: lmnew not even length"
        #print("eta:",eta,"\nnew landmark",lmnew)
        etaadded = np.block([eta,lmnew])  # TODO, append new landmarks to state vector
        # print("\n Shape etaadded:",np.shape(etaadded))
        # TODO, block diagonal of P_new, see problem text in 1g) in graded assignment 3

        # print("shape P : ",np.shape(P), "\n shape Gx", np.shape(Gx))
        # print("shape Gz: ",np.shape(Gz))
        # print("\nn",n) 
        # Padded
        block2 = Gx@P[0:3,0:3]@Gx.T+Rall
        Padded = block_diag(P,block2)

        # print("shape Padded : ",np.shape(Padded))
        
        Pcolon_x =P[:,0:3]
        # print("Pcolon_x",Pcolon_x)

        Padded[:n, n:] =Pcolon_x@Gx.T  # TODO, top right corner of P_new
        # print("\nshape:",np.shape(Padded[:n, n:]))
        # TODO, transpose of above. Should yield the same as calcualion, but this enforces symmetry and should be cheaper
        Padded[n:, :n] = Padded[:n, n:].T
        # print("Correct etaadded",etaadded_correct)
        # print("\nTest: etaadded",etaadded)
        # print("Test: Padded compare",Padded_correct[n:, :n]-Padded[n:, :n])
        # print("\n Test: Padded",Padded)
        assert (
            etaadded.shape * 2 == Padded.shape
        ), "EKFSLAM.add_landmarks: calculated eta and P has wrong shape"
        assert np.allclose(
            Padded, Padded.T
        ), "EKFSLAM.add_landmarks: Padded not symmetric"
        assert np.all(
            np.linalg.eigvals(Padded) >= 0
        ), "EKFSLAM.add_landmarks: Padded not PSD"

        return etaadded, Padded

    def associate(
        self, z: np.ndarray, zpred: np.ndarray, H: np.ndarray, S: np.ndarray,
    ):  # -> Tuple[*((np.ndarray,) * 5)]:
        """Associate landmarks and measurements, and extract correct matrices for these.

        Parameters
        ----------
        z : np.ndarray,
            The measurements all in one vector
        zpred : np.ndarray
            Predicted measurements in one vector
        H : np.ndarray
            The measurement Jacobian matrix related to zpred
        S : np.ndarray
            The innovation covariance related to zpred

        Returns
        -------
        Tuple[*((np.ndarray,) * 5)]
            The extracted measurements, the corresponding zpred, H, S and the associations.

        Note
        ----
        See the associations are calculated  using JCBB. See this function for documentation
        of the returned association and the association procedure.
        """
        if self.do_asso:
            # Associate
            a = JCBB(z, zpred, S, self.alphas[0], self.alphas[1])

            # Extract associated measurements
            zinds = np.empty_like(z, dtype=bool)
            zinds[::2] = a > -1  # -1 means no association
            zinds[1::2] = zinds[::2]
            zass = z[zinds]

            # extract and rearange predicted measurements and cov
            zbarinds = np.empty_like(zass, dtype=int)
            zbarinds[::2] = 2 * a[a > -1]
            zbarinds[1::2] = 2 * a[a > -1] + 1

            zpredass = zpred[zbarinds]
            Sass = S[zbarinds][:, zbarinds]
            Hass = H[zbarinds]

            assert zpredass.shape == zass.shape
            assert Sass.shape == zpredass.shape * 2
            assert Hass.shape[0] == zpredass.shape[0]

            return zass, zpredass, Hass, Sass, a
        else:
            # should one do something her
            pass

    def update(
        self, eta: np.ndarray, P: np.ndarray, z: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, float, np.ndarray]:
        """Update eta and P with z, associating landmarks and adding new ones.
        Parameters
        ----------
        eta : np.ndarray
            [description]
        P : np.ndarray
            [description]
        z : np.ndarray, shape=(#detections, 2)
            [description]
        Returns
        -------
        Tuple[np.ndarray, np.ndarray, float, np.ndarray]
            [description]
        """
        # # TODO replace this with your own code
        # etaupd_sol, Pupd_sol, NIS_sol, a_sol = solution.EKFSLAM.EKFSLAM.update(self, eta, P, z)
        # return etaupd, Pupd, NIS, a

        numLmk = (eta.size - 3) // 2
        assert (len(eta) - 3) % 2 == 0, "EKFSLAM.update: landmark lenght not even"

        if numLmk > 0:
            # Prediction and innovation covariance
            zpred = self.h(eta)  # TODO
            H = self.h_jac(eta) # TODO

            # Here you can use simply np.kron (a bit slow) to form the big (very big in VP after a while) R,
            # or be smart with indexing and broadcasting (3d indexing into 2d mat) realizing you are adding the same R on all diagonals

            # S = H@P@H.T + self.R # TODO,
            big_R = np.kron(np.eye((numLmk)),self.R)
            S = H@P@H.T + big_R

            assert (
                S.shape == zpred.shape * 2
            ), "EKFSLAM.update: wrong shape on either S or zpred"
            z = z.ravel()  # 2D -> flat

            # Perform data association
            za, zpred, Ha, Sa, a = self.associate(z, zpred, H, S)

            # No association could be made, so skip update
            if za.shape[0] == 0:
                etaupd = eta
                Pupd = P
                NIS = 1  # TODO: beware this one when analysing consistency.
            else:
                # print("# Create the associated innovation")
                # Create the associated innovation
                v = za.ravel() - zpred  # za: 2D -> flat
                v[1::2] = utils.wrapToPi(v[1::2])

                # Kalman mean update
                # S_cho_factors = la.cho_factor(Sa) # Optional, used in places for S^-1, see scipy.linalg.cho_factor and scipy.linalg.cho_solve
                S,low = la.cho_factor(Sa)
                S_inv = la.cho_solve((S,low),np.eye(Sa.shape[0]))

                W = P@Ha.T@S_inv  # TODO, Kalman gain, can use S_cho_factors

                etaupd = eta + W@v # TODO, Kalman update

                # Kalman cov update: use Joseph form for stability
                jo = -W @ Ha
                # same as adding Identity mat
                jo[np.diag_indices(jo.shape[0])] += 1

                dim_big_R = int(W.shape[1]/2)
                big_R = np.kron(np.eye(dim_big_R),self.R)

                # num_asso = za.shape[0]
                # big_R = big_R[0:num_asso,0:num_asso]
                

                # print("num_asso", num_asso)
                # print("jo@P@jo.T", np.shape(jo@P@jo.T))
                # print("W,", np.shape(W))
                # print("big_R", np.shape(big_R))
                

                Pupd = jo@P@jo.T + W@big_R@W.T  # TODO, Kalman update. This is the main workload on VP after speedups


                # Pupd = jo@P

                # calculate NIS, can use S_cho_factors
                NIS = v.T@S_inv@v  # TODO

                # When tested, remove for speed
                assert np.allclose(
                    Pupd, Pupd.T), "EKFSLAM.update: Pupd not symmetric"
                assert np.all(
                    np.linalg.eigvals(Pupd) > 0
                ), "EKFSLAM.update: Pupd not positive definite"

        else:  # All measurements are new landmarks,
            a = np.full(z.shape[0], -1)
            z = z.flatten()
            NIS = 1  # TODO: beware this one when analysing consistency.
            # print("# All measurements are new landmarks")
            etaupd = eta
            Pupd = P

        # Create new landmarks if any is available
        if self.do_asso:
            is_new_lmk = a == -1
            if np.any(is_new_lmk):
                # print("# Create new landmarks if any is available")
                z_new_inds = np.empty_like(z, dtype=bool)
                z_new_inds[::2] = is_new_lmk
                z_new_inds[1::2] = is_new_lmk
                z_new = z[z_new_inds]
                etaupd, Pupd = self.add_landmarks(etaupd, Pupd, z_new)#None  # TODO, add new landmarks.

        assert np.allclose(
            Pupd, Pupd.T), "EKFSLAM.update: Pupd must be symmetric"
        assert np.all(np.linalg.eigvals(Pupd) >=
                      0), "EKFSLAM.update: Pupd must be PSD"

        # print("etaupd",etaupd_sol - etaupd)
        # print("Pupd", Pupd - Pupd_sol)
        # print("NIS", NIS - NIS_sol)
        # print("a", a - a_sol)

        return etaupd, Pupd, NIS, a

    @classmethod
    def NEESes(cls, x: np.ndarray, P: np.ndarray, x_gt: np.ndarray,) -> np.ndarray:
        """Calculates the total NEES and the NEES for the substates
        Args:
            x (np.ndarray): The estimate
            P (np.ndarray): The state covariance
            x_gt (np.ndarray): The ground truth
        Raises:
            AssertionError: If any input is of the wrong shape, and if debug mode is on, certain numeric properties
        Returns:
            np.ndarray: NEES for [all, position, heading], shape (3,)
        """

        assert x.shape == (3,), f"EKFSLAM.NEES: x shape incorrect {x.shape}"
        assert P.shape == (3, 3), f"EKFSLAM.NEES: P shape incorrect {P.shape}"
        assert x_gt.shape == (
            3,), f"EKFSLAM.NEES: x_gt shape incorrect {x_gt.shape}"

        d_x = x - x_gt
        d_x[2] = utils.wrapToPi(d_x[2])
        assert (
            -np.pi <= d_x[2] <= np.pi
        ), "EKFSLAM.NEES: error heading must be between (-pi, pi)"

        d_p = d_x[0:2]
        P_p = P[0:2, 0:2]
        assert d_p.shape == (2,), "EKFSLAM.NEES: d_p must be 2 long"
        d_heading = d_x[2]  # Note: scalar
        assert np.ndim(
            d_heading) == 0, "EKFSLAM.NEES: d_heading must be scalar"
        P_heading = P[2, 2]  # Note: scalar
        assert np.ndim(
            P_heading) == 0, "EKFSLAM.NEES: P_heading must be scalar"

        # NB: Needs to handle both vectors and scalars! Additionally, must handle division by zero
        NEES_all = d_x @ (np.linalg.solve(P, d_x))
        NEES_pos = d_p @ (np.linalg.solve(P_p, d_p))
        try:
            NEES_heading = d_heading ** 2 / P_heading
        except ZeroDivisionError:
            NEES_heading = 1.0  # TODO: beware

        NEESes = np.array([NEES_all, NEES_pos, NEES_heading])
        NEESes[np.isnan(NEESes)] = 1.0  # We may divide by zero, # TODO: beware

        assert np.all(NEESes >= 0), "ESKF.NEES: one or more negative NEESes"
        return NEESes
