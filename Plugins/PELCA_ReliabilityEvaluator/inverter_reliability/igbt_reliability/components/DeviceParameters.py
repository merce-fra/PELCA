# -*- coding: utf-8 -*-
"""\brief Store semiconductor electrical and thermal parameters used by loss models.

This module is part of the PELCA reliability evaluator.
"""

import numpy as np

# =====================================================
# Calculate the losses within the diode and transistor branches of the reference module.
# =====================================================
# Adapted to use loss functions defined for the selected reference module.
# Parameter values should be checked against the selected power-module datasheet.

class DeviceParameters:
    """ contains the parameters and methods to enable calculation of losses within IGBT  and diode
    of power module (reference_module); contains also the thermal parameters required by thermal model of diode
    or IGBT (virtual junction to case model for "IGBT" (composed actually of 3 dies in //, but considered
    as component "IGBT"; same for "diode")
    """
    # note that some functions take output current as parameter while current in module is expected
    #(for losses calculations). This is the reason why parameter nb_parallel_sw is used here.


    def __init__(self, params):

        # <those parameters are normally defined in excel sheet>
        # note: second argument of params.get defines default value if parameter is missing in file
        """Initialize the object with the provided configuration."""
        self.Rg = params.get('Rg',6.67)          # ohm  (impacts the sw losses...)

        self.DC_BUS_V = params.get('Udc', 540)                # DC bus voltage

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.nb_parallel_sw = params.get('nb_parallel_sw',2)  # not a characteristic of reference_module but rather of converter topology parameter...
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # ==========================
        # switching loss parameters
        # ==========================

        # self.I_ref_sw = 50.0   # A, Reference current for switching energy

        # switching losses coef of fitting functions
        # self.E_on_ref = 5.0e-3 # J, Turn-on energy @ I_ref_sw @ T_ref_loss  (IGBT)

        self.EON_0    = params.get('EON_0',7.74e+00)  # in mJ
        self.ICON_1   = params.get('ICON_1', 3.72e-02)
        self.ICON_2   = params.get('ICON_2', 6.61e-05)

        self.TCON     = params.get('TCON', 6.00e-04)
        self.VCON     = params.get('VCON', 1.3)
        self.RgCON    = params.get('RgCON', 0.55)

        # self.E_off_ref = 4.0e-3# J, Turn-off energy @ I_ref_sw @ T_ref_loss (IGBT)

        self.EOFF_0   = params.get('EOFF_0', 1.05E+01)  # in mJ
        self.ICOFF_1  = params.get('ICOFF_1', 7.54E-02)
        self.ICOFF_2  = params.get('ICOFF_2', 2.10E-05)
        self.TCOFF    = params.get('TCOFF', 7.25E-03)
        self.VCOFF    = params.get('VCOFF', 1.3)
        self.RgCOFF   = params.get('RgCOFF', 3.57E-02)

        # E_on_off_ref_sum = self.E_on_ref + self.E_off_ref
        # self.E_temp_coeff_IGBT  = 0.001 * E_on_off_ref_sum / 10.0 # J/K (Total E_sw change per K)
        # self.E_temp_coeff_DIODE = 0.001 * self.E_rec_ref / 10.0 # J/K (E_rec change per K)

        # recovery losses parameters
        # self.E_rec_ref = 3.0e-3# J, Diode reverse recovery energy @ I_ref_sw @ T_ref_loss

        self.ERR_0    = params.get('ERR_0', 1.90E+01)  # in mJ
        self.ICRR_1   = params.get('ICRR_1', 7.12E-02)
        self.ICRR_2   = params.get('ICRR_2', -3.55E-05)
        self.TCRR     = params.get('TCRR', 7.94E-03)
        self.VCRR     = params.get('VCRR', 0.6)
        self.RgCRR    = params.get('RgCRR', -9.30E-02)

        # # Temperature Dependence Parameters
        # self.T_ref_loss = 100.0      # deg C, Reference temperature for Rce/Rf/Esw
        self.Tj_ref   = params.get('Tj_ref', 150)
        self.Rg_ref   = params.get('Rg_ref', 1)
        self.Vbus_ref = params.get('Vbus_ref', 600)

        # ==========================
        # conduction loss parameters
        # ==========================

        # # for conduction losses - page fitreference_moduleDiode_linear ???
        # # Vth shift
        # self.Vth_shift_cross_point = 1.082953    # V
        # self.Vth_shift_slope       = -0.0004322  # V/K
        # # slope change
        # self.slope_change_cross_point = 0.0008171
        # self.slope_change_slope = 1.056E-06

        # excel sheet Si-Vce_reference power module_Diode_linear <used?>
        # D_V_OC, D_KV, D_RON_OC, D_KROhm
        self.V_OC   = params.get('V_OC', 1.09603070059454)        # V
        self.Kv     = params.get('Kv', -0.000746064369102834)     # V/K
        self.RON_OC = params.get('RON_OC', 0.000817071250259659)  # Ohm
        self.KROhm  = params.get('KROhm', 1.05565962463445E-06)   # Ohm/K

        # self.Vf0 = 0.9         # V, Diode threshold voltage
        # self.Rf_ref = 0.005    # Ohm, Diode resistance @ T_ref_loss
        # self.Rf_temp_coeff = 3.0e-5  # Ohm/K, Conduction resistance increase per Kelvin for Diode

        #Rterminal model
        self.Rterminal = params.get('Rterminal', 2.28776E-05)
        self.KRterminal = params.get('KRterminal', 3.52111E-06)

        #diode, "power" model
        self.D_k11 = params.get('D_k11', 0.0000481040000842165)
        self.D_k12 = params.get('D_k12', 0.016018960082333)
        self.D_k21 = params.get('D_k21', -0.000132032526444804)
        self.D_k22 = params.get('D_k22', 0.625614554906918)
        self.D_k31 = params.get('D_k31', -0.00159023340191401)
        self.D_k32 = params.get('D_k32', 0.721755529844096)

        # Excel sheet Si-Vce_reference power module_IGBT_linear (sufficient?)
        self.T_V_OC   = params.get('T_V_OC', 1.02516062967014)       # V
        self.T_Kv     = params.get('T_Kv', -0.00101520482681338)     # V/K
        self.T_RON_OC =params.get('T_RON_OC',  0.000714113801214027) # Ohm
        self.T_KROhm  = params.get('T_KROhm', 4.93035008629898E-06)  # Ohm/K

        # self.Vce0 = 0.8        # V, IGBT Collector-Emitter threshold voltage
        # self.Rce_ref = 0.008   # Ohm, IGBT Collector-Emitter resistance @ T_ref_loss
        # self.Rce_temp_coeff = 5.0e-5 # Ohm/K, Conduction resistance increase per Kelvin for IGBT

        # IGBT, "Power" model
        self.T_k11 =	params.get('T_k11', 0.0000483884020346818) # 4.839E-05
        self.T_k12 =	params.get('T_k12', 0.0167485038440915)    # 1.675E-02
        self.T_k21 =	params.get('T_k21', 0.000167554663735255 ) # 1.676E-04
        self.T_k22 =	params.get('T_k22', 0.608755001792953)     # 6.088E-01
        self.T_k31 =	params.get('T_k31', -0.00164580661708131)  #-1.646E-03
        self.T_k32 =	params.get('T_k32', 0.648512439086945)     # 6.485E-01


        # 4. Thermal Parameters (Junction-to-Case - 4th Order FOSTER MODEL)
        self.Rth_jc_Q = params.get('Rth_jc_Q', 48) # K/kW
        self.Rth_jc_D = params.get('Rth_jc_D', 76) # K/kW

        # to update with excel data
        self.Rth_IGBT = np.array([0.0457, 0.2737, 0.3178, 0.3628])*self.Rth_jc_Q*1e-3  # K/W
        self.tau_IGBT = np.array([3.5483e-04, 1.0343e-02 , 7.3012e-02, 7.3015e-02])

        self.Cth_IGBT = self.tau_IGBT/self.Rth_IGBT
        #self.Cth_IGBT = np.array([0.001, 0.01, 0.1, 1.0])

        # to update with excel data
        self.Rth_Diode = np.array([0.0457, 0.2737, 0.3178, 0.3628])*self.Rth_jc_D*1e-3 # K/W
        self.tau_Diode = np.array([3.5483e-04, 1.0343e-02 , 7.3012e-02, 7.3015e-02])

        self.Cth_Diode = self.tau_Diode/self.Rth_Diode
        #self.Cth_Diode = np.array([0.002, 0.02, 0.2, 2.0])

        self.Rth_jc_IGBT_avg  = self.Rth_IGBT.sum()
        self.Rth_jc_Diode_avg = self.Rth_Diode.sum()

    # ============================
    # switching losses calculation
    # ============================
    # IGBT turn-on (as function of Tj, Rg, DC bus voltage and current)
    # in mJ (instead of J)
    def eon(self, Tj, Rg, V_bus, Ic):
        """Run eon."""
        Eon = (self.EON_0 + (self.ICON_1*Ic + self.ICON_2*Ic**2) *
                (1+self.TCON*(Tj-self.Tj_ref))*(1+self.RgCON*(Rg-self.Rg_ref)) *
                ((V_bus/self.Vbus_ref)**self.VCON))
        #print("Eon:",Eon)
        return Eon

    # IGBT turn-off losses
    # in mJ (instead of J)
    def eoff(self, Tj, Rg, V_bus, Ic):
        """Run eoff."""
        Eoff = (self.EOFF_0 + (self.ICOFF_1*Ic + self.ICOFF_2*Ic**2) *
                (1+self.TCOFF*(Tj-self.Tj_ref))*(1+self.RgCOFF*(Rg-self.Rg_ref)) *
                ((V_bus/self.Vbus_ref)**self.VCOFF))
        #print("Eoff:",Eoff)
        return Eoff

    # FW diode recovery losses
    # in mJ (instead of J)
    def err(self, Tj, Rg, Vbus, Ic):
        """Run err."""
        Err = (self.ERR_0 + (self.ICRR_1*Ic + self.ICRR_2*Ic**2) *
                (1+self.TCRR*(Tj-self.Tj_ref))*(1+self.RgCRR*(Rg-self.Rg_ref)) *
                ((Vbus/self.Vbus_ref)**self.VCRR))
        #print("Err:",Err)
        return Err

    # scaling of switching energy for IGBT
    # ET : Switching loss energy of the power transistor (IGBT) per volt and per ampere
    def ET(self, T, Vbus, Ic, Rg):

        # Ic is the switched current within one power module here
        #if Ic==0:
        #    return 0
        #else:
        #    return (self.eon(T, Rg, Vbus, Ic)+self.eoff(T, Rg, Vbus, Ic))/(Vbus*Ic)
        """Run e t."""
        if isinstance(Ic, float):
            if Ic==0:
                return 0
            else:
                IGBT_sw_losses = (self.eon(T, Rg, Vbus, Ic) + self.eoff(T, Rg, Vbus, Ic)) / (Vbus*Ic)
                if IGBT_sw_losses is None:
                    print('Ic',Ic)
            return IGBT_sw_losses
        else:
            # not a float... but <class 'numpy.ndarray'>

            """
            Calculates ET = (eon + eoff) / (Vbus * Ic), puting 0 where Ic == 0.
            Accepts T, Vbus, Ic, Rg as scalar or ndarrays broadcastable ndarrays.
            Return an array or a scalar depending on inputs.
            """
            Ic_arr    = np.asarray(Ic)
            Vbus_arr  = np.asarray(Vbus) #  could still be a scalar
            T_arr     = np.asarray(T)    #  "
            Rg_arr    = np.asarray(Rg)   #  "

            out_shape = np.broadcast(Ic_arr, Vbus_arr, T_arr, Rg_arr).shape
            out_dtype = np.result_type(T_arr, Vbus_arr, Ic_arr, np.float64)
            out = np.zeros(out_shape, dtype=out_dtype)

            # masks positions where Ic !=0
            mask = Ic_arr != 0
            mask = np.broadcast_to(mask, out_shape)

            if np.any(mask):
                # broadcast all inputs with the same shape
                Ic_b   = np.broadcast_to(Ic_arr,   out_shape)
                Vbus_b = np.broadcast_to(Vbus_arr, out_shape)
                T_b    = np.broadcast_to(T_arr,    out_shape)
                Rg_b   = np.broadcast_to(Rg_arr,   out_shape)

                # Calculate numerator only on valid positions
                num = np.empty(out_shape, dtype=out_dtype)
                num[mask] = (
                    self.eon(T_b[mask], Rg_b[mask], Vbus_b[mask], Ic_b[mask]) +
                    self.eoff(T_b[mask], Rg_b[mask], Vbus_b[mask], Ic_b[mask])
                    )

                # Division (zero elsewhere because it is initialized to 0)
                np.divide(num, Vbus_b * Ic_b, out=out, where=mask)

                # if the shape is scalar, return a float instead of ndarray 0-D
                # debug
                #print('ET: type(out):',type(out))
                return out.item() if out_shape == () else out

    # 125degC / 540 V / Ic (A) / Rg (ohm)
    # c.ET(125, 540, 373/2, 6.67) = 6.32e-7

    # in Excel sheet:
    # ET = 0,001*(EON (Tj, Ic,out,package, Ibus,Rg)+EOFF (Tj, Ic,out,package, Ibus,Rg))/(Ic*Vbus)
    # ? (switching losses normally)
    # with Ic=current for conduction losses calculations, per package =  current for conduction losses calculations, per switch / 2
    # current for conduction losses calculations, per switch = motor current + motor cable current (10A)
    # ?


    # scaling of switching energy for diode
    # ED : Switching loss energy of the power diode per volt and per ampere
    def ED(self, T, Vbus, Ic, Rg):
        """Run e d."""
        if isinstance(Ic, float):
            # Ic is the switched current within one power module here
            if Ic==0:
                return 0
            else:
                diode_recov_losses = self.err(T, Rg, Vbus, Ic)/(Vbus*Ic)
                if diode_recov_losses is None:
                    print('Ic',Ic)
            return diode_recov_losses
        else:
            # not a float... but <class 'numpy.ndarray'>
            return self.err(T, Rg, Vbus, Ic)/(Vbus*Ic)

    # c.ED(125,540,373/2,6.67) : 2.31e-7

    # in Excel sheet:
    # ED = 0,001*(ERR (Tj, Ic,out,package, Ibus,Rg))/(current for switching loss calculations, per package * Vbus)
    # current for switching loss calculations, per package = current for switching loss calculations, per switch/2
    # current for switching loss calculations, per switch = Iout+motor cable current

    # =============================
    # conduction losses calculation
    # =============================

    # ======================================================================
    # parameters for IEC TC 22 calculation

    # based on linear models (maybe better to base them on more complicated models)
    # # supposed to be IGBT parameters
    # def UT_th(self, T ):
    #     return self.T_V_OC + self.T_Kv*T
    # def UT_r(self, T, rated_current):
    #     return (self.T_V_OC + self.T_Kv * T
    #             + rated_current*(self.T_RON_OC + T*self.T_KROhm ))

    # in Excel sheet
    # K11... igbt
    # Icond = Iout of inverter here => only half this current goes in one module (if two modules in //)
    # Voc + Kv*T + k12 ???
    # Vce(T, I_module)
    def UT_r(self, Tj_igbt, Icond):
        """Run u t r."""
        Iout_package = Icond /  self.nb_parallel_sw
        # =(($F$21*G76+$F$22)*G$60^($F$23*G76+$F$24))+$F$25*G76+$F$26
        return ((self.T_k11*Tj_igbt + self.T_k12) * Iout_package**(self.T_k21*Tj_igbt + self.T_k22)) + self.T_k31*Tj_igbt + self.T_k32
    #c.UT_r(125,363) = 1.05
    # used by UT_th

    # UT_th = UT_r - Iout_package*slope_of_ic_vce
    def UT_th(self, Tj_igbt, Icond):
        """
        calculate IGBT threshold voltage (linearized model)
        :param Tj_igbt: junction temperature of IGBT
        :param Icond: conduction current value (divided if modules connected in //)
        :return: Uth value
        """
        # Icond = Iout of inverter here => only half this current goes in one module (if two modules in //)
        if isinstance(Icond, float):
            if Icond != 0:
                # -((6*($F$21*G76+$F$22)/($F$23*G76+$F$24+1))-12*(($F$21*G76+$F$22)/($F$23*G76+$F$24+2)))*G$60^($F$23*G76+$F$24-1)
                Iout_package = Icond / self.nb_parallel_sw # Iout_package = current for conduction losses calculations, per switch/2  (= current in one module)
                slope_of_ic_vce = -((6 * (self.T_k11*Tj_igbt + self.T_k12)/(self.T_k21*Tj_igbt + self.T_k22 + 1))
                                    -12*((self.T_k11*Tj_igbt + self.T_k12)/(self.T_k21*Tj_igbt + self.T_k22 + 2)))*Iout_package**(self.T_k21*Tj_igbt + self.T_k22-1)
                #print("self.T_k21*Tj_igbt + self.T_k22-1:", self.T_k21*Tj_igbt + self.T_k22-1)
                return self.UT_r(Tj_igbt, Icond) - Iout_package*slope_of_ic_vce
            else:  #Icond=0
                return self.UT_r(Tj_igbt, Icond)
        else:

            Iout_package = Icond /  self.nb_parallel_sw # Iout_package = current for conduction losses calculations, per switch/2  (=> current in one module)
            slope_of_ic_vce = -((6 * (self.T_k11*Tj_igbt + self.T_k12)/(self.T_k21*Tj_igbt + self.T_k22 + 1))
                                -12*((self.T_k11*Tj_igbt + self.T_k12)/(self.T_k21*Tj_igbt + self.T_k22 + 2)))*Iout_package**(self.T_k21*Tj_igbt + self.T_k22-1)
            #print("self.T_k21*Tj_igbt + self.T_k22-1:", self.T_k21*Tj_igbt + self.T_k22-1)
            return self.UT_r(Tj_igbt, Icond) - Iout_package*slope_of_ic_vce
    # c.UT_th(125,363) = 0.51


    # supposed to be DIODE parameters
    # def UD_th(self, T):
    #     return self.V_OC + self.Kv*T # Threshold voltage  of the power diode
    # def UD_r (self, T, rated_current):
    #     return (self.V_OC + self.Kv * T
    #             + rated_current*(self.RON_OC + T*self.KROhm ))  # On state voltage of the power diode at rated CDM output current

    # in excel sheet:
    # K11 ... diode
    # UD_th = UD_r-Iout_package*slope_of_ic_vce
    # UD_r  = ((K11*Tj_diode + K12)*Iout_package^(K21*Tj_diode + K22)) + K31*Tj_diode + K32
    # slope_of_ic_vce = -((6*(K11*Tj_diode+K12)/(K21*Tj_diode+K22+1))-12*((K11*Tj_diode+K12)/(K21*Tj_diode+K22+2)))*Iout_package^(K21*Tj_diode+K22-1)

    # Icond = Iout of inverter here => only half this current goes in one module
    def UD_r(self, Tj_diode, Icond):
        """Run u d r."""
        Iout_package = Icond /  self.nb_parallel_sw
        return ((self.D_k11*Tj_diode + self.D_k12)*Iout_package**(self.D_k21*Tj_diode + self.D_k22))+ self.D_k31*Tj_diode + self.D_k32
    #c.UD_r(125,363) = 1.047

    # UT_r - Iout_package*slope_of_ic_vce
    # Icond = Iout of inverter here => only half this current goes in one module
    def UD_th(self, Tj_diode, Icond):
        """Run u d th."""
        if isinstance(Icond, float):
            if Icond != 0:
                Iout_package = Icond /  self.nb_parallel_sw # Iout_package = current for conduction losses calculations, per switch/2  (=> courent in one module)
                slope_of_ic_vce = -((6 * (self.D_k11*Tj_diode + self.D_k12)/(self.D_k21*Tj_diode + self.D_k22 + 1))
                                    -12*((self.D_k11*Tj_diode + self.D_k12)/(self.D_k21*Tj_diode + self.D_k22 + 2)))*Iout_package**(self.D_k21*Tj_diode + self.D_k22-1)
                #print("slope_of_ic_vce: ",slope_of_ic_vce)
                return self.UD_r(Tj_diode, Icond) - Iout_package*slope_of_ic_vce
            else:
                return self.UD_r(Tj_diode, Icond)
        else:
            Iout_package = Icond /  self.nb_parallel_sw # Iout_package = current for conduction losses calculations, per switch/2  (=> courent in one module)
            slope_of_ic_vce = -((6 * (self.D_k11*Tj_diode + self.D_k12)/(self.D_k21*Tj_diode + self.D_k22 + 1))
                                -12*((self.D_k11*Tj_diode + self.D_k12)/(self.D_k21*Tj_diode + self.D_k22 + 2)))*Iout_package**(self.D_k21*Tj_diode + self.D_k22-1)
            #print("slope_of_ic_vce: ",slope_of_ic_vce)
            return self.UD_r(Tj_diode, Icond) - Iout_package*slope_of_ic_vce
    # c.UD_th(125,363) = 0.59


    #note: Vbus, Rg are already defined in the class ... DC_BUS_V



    # ======================================================================
    # diode
    # I_E : emitter current (free wheeling diode forward characteristic)
    # <3 diodes in // : considered here? (terminal resistance)>

    # "linear" model
    def Vce_term(self, I_E, T):
        """Run vce term."""
        return (self.V_OC + self.Kv * T
                +I_E*(self.RON_OC + T*self.KROhm)
                +I_E*(self.Rterminal+self.KRterminal*T))
   # Vec

    # Diode
    # "power" model - better? (more accurate at low current...)
    def Vce_datasheet(self, I_E, T):
        """Run vce datasheet."""
        return ((self.D_k11 * T + self.D_k12) *
                I_E**(self.D_k21 * T + self.D_k22)
                + self.D_k31 * T + self.D_k32)
    #Vec
    # ===========================================================

    # ===========================================================
    # IGBT
    # linear model Vce_sat = f(Ic, T)
    def Vce_sat(self, I_C, T):
        """Run vce sat."""
        return (self.T_V_OC + self.T_Kv * T +
                I_C*(self.T_RON_OC + T*self.T_KROhm))

    # IGBT "power" model - better? (more accurate at low current...)
    def T_Vce_datasheet(self, I_E, T):
        """Run t vce datasheet."""
        return ((self.T_k11 * T + self.T_k12) *
                I_E**(self.T_k21 * T + self.T_k22)
                + self.T_k31 * T + self.T_k32)
    # ===========================================================

if __name__ == '__main__':
    # check
    params = {}
    c = DeviceParameters(params)
    print("Eon losses at Ic=0A :", c.eon(150, 6.6666, 540, 0), "mJ")
    print("Eon losses at Ic=150A :",c.eon(150, 6.6666, 540, 150), "mJ")
    print("Eon losses at Ic=600A :",c.eon(150, 6.6666, 540, 600), "mJ")

    print("Eoff losses at Ic=0A :", c.eoff(150, 6.6666, 540, 0), "mJ")
    print("Eoff losses at Ic=150A :",c.eoff(150, 6.6666, 540, 150), "mJ")
    print("Eoff losses at Ic=600A :",c.eoff(150, 6.6666, 540, 600), "mJ")

    print("Err losses at Ic=0A :", c.err(150, 6.6666, 540, 0), "mJ")
    print("Err losses at Ic=150A :",c.err(150, 6.6666, 540, 150), "mJ")
    print("Err losses at Ic=600A :",c.err(150, 6.6666, 540, 600), "mJ")

    print("UT_th at 100degC, 363A: ", c.UT_th(100, 333 ))
    print("UT_r  at 100degC, 363A: ", c.UT_r(100, 363 ))

    # reference power module : Vec_terminals = 1.95V (@600A, Tvj=150degC)


    for i in np.arange(0,120,20):
        print(f"diode Vce = f(IE, 125degC), for I = {i} A:", c.Vce_term(i, 125))

    for i in np.arange(0,120,20):
        print(f"diode Vce_datasheet = f(IE, 125degC), for I = {i} A:", c.Vce_datasheet(i, 125))

    for i in np.arange(0,120,20):
        print(f"IGBT Vce_sat = f(Ic, 125degC), for I = {i} A:", c.Vce_sat(i, 125))

    # switching losses as function of current
    import matplotlib.pyplot as plt
    Tj_m=80
    i=np.arange(100,600,10)

    plt.plot(i,c.ED(Tj_m,540,i,2.2))
    plt.title("ED vs current")
    plt.xlabel("current")
    plt.ylabel("ED")
    plt.show()

    plt.plot(i,c.ET(Tj_m,540,i,2.2)) # quite "constant" between 300 & 600
    plt.title("ET vs current")
    plt.xlabel("current")
    plt.ylabel("ET")
    plt.show()

    plt.plot(i, c.UT_th(100, i ))
    plt.plot(i, c.UT_r(100, i))
    plt.title("UT_th, UT_r vs current (at 100degC)")
    plt.xlabel("current")
    plt.ylabel("U")
    plt.show()


    # calculation of ET for half a fout period
    fout=50
    fsw=2000
    Iout_rms=363
    Tj_m = 80
    Vdc = 540
    Time_vect = np.arange(0.001,(1/fout)/2,1/fsw)
    current_vect = np.sin(2*np.pi*fout*Time_vect)*Iout_rms*np.sqrt(2)
    ET_vect = c.ET(Tj_m,Vdc,current_vect,2.2)

    plt.plot(Time_vect,ET_vect)
    plt.title("ET switch energy over half a fout period")
    plt.xlabel("time")
    plt.ylabel("ET")
    plt.show()
    # np.mean(ET_vect)                     : 0.0003469
    # c.ET(Tj_m,Vdc,363,2.2)               : 0.000319
    # np.sqrt(np.mean(np.square(ET_vect))) : 0.000353
