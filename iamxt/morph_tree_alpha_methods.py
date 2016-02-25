# -*- encoding: utf-8 -*-
# Module morph_tree_bbox

import copy
import numpy as np
import cv2
import os
import warnings

try:
    import gvgen
except:
    warnings.warn("gvgen not installed, this may cause a problem in drawing functions")

try:
    import StringIO
except:
    warnings.warn("StringIO not installed, this may cause a problem in drawing functions")

def bbox(self, dx, dy, dz = 0):
    """
    Contracts all nodes with bounding box less than 'dx' by 'dy'
    """
    ddx = self.node_array[7,:] - self.node_array[6,:] + 1
    ddy = self.node_array[10,:] - self.node_array[9,:] + 1
    if self.node_index.ndim == 2:
        self.prune((ddx < dx) & (ddy < dy))
    else:
        ddz = self.node_array[13,:] - self.node_array[12,:] + 1
        self.prune((ddx < dx) & (ddy < dy) & (ddz < dz))
    return self

def clone(self):
    """
    This method returns a hard copy of the Max-Tree object.
    """
    mxt = copy.deepcopy(self)
    return mxt

def compact(self, to_remove, lut):
    """
    This method removes the nodes to_remove of self.node_array and adjust 
    the pointers in self.node_array and self.node_index. to_remove is a boolean
    array with 1 for the nodes that need to be removed. 
    """
    self._children_updated = False 
    self._sb_updated = False 
    N = self.node_array.shape[1]
    parent = self.node_array[0,:]
    index_fix = to_remove.astype(np.int32).cumsum()
    lut = (lut - index_fix[lut]).astype(np.int32)
    self.node_array[0,:] = lut[parent]

    if self.node_index.ndim == 3:
        self.lut_node_index_3d_aux(lut,self.node_index)
    else:    
        self.lut_node_index_2d_aux(lut,self.node_index)
        
    #self.node_array = self.node_array[:,~to_remove]
    #if not self.node_array.flags.contiguous:
    #    self.node_array = np.ascontiguousarray(self.node_array, dtype = np.int32)
        
    nodes_kept = np.nonzero(~to_remove)[0].astype(np.int32)
    new_node_array = np.empty((self.node_array.shape[0],nodes_kept.size), dtype = np.int32)    
    self.remove_node_array_lines_aux(nodes_kept,new_node_array,self.node_array)
    self.node_array = new_node_array
    return self



def areaOpen(self, n):
    """
    Contracts all the nodes with area less than 'area'
    """
    area = self.node_array[3,:]
    self.prune(area <= n)
    return self

def getImage(self):
    """
    This method returns the image corresponding to the tree.
    """
    out_img = np.empty(self.node_index.shape, dtype = np.uint16)
    if self.node_index.ndim == 3:
        self.get_image_aux_3d_aux(self.node_array[2],self.node_index,out_img)
    else:
        self.get_image_aux_2d_aux(self.node_array[2],self.node_index,out_img)
    return out_img.astype(self.ftype)



def computeRR(self):
    xmin,xmax = self.node_array[6,:], self.node_array[7,:] + 1
    ymin,ymax = self.node_array[9,:], self.node_array[10,:] + 1
    area = self.node_array[3,:]

    if self.node_index.ndim == 2:
        return 1.0*area/((xmax-xmin)*(ymax-ymin))
    else:
        zmin,zmax = self.node_array[12,:], self.node_array[13,:] + 1
        return 1.0*area/((xmax-xmin)*(ymax-ymin)*(zmax-zmin))


def prune(self, to_prune):
    """
    Contracts entire branches of the tree. This is the prunning procedure to be
    used for the non-increasing
    connected filters. If a node is indicated in to_prune, all its descendants
    should also be indicated in to_prune.
    """
    N = self.node_array.shape[1]
    lut = np.arange(N, dtype = np.int32)
    self.prune_aux(lut,to_prune.astype(np.int32), self.node_array[0,:], self.node_array[1,:])
    self.node_index = lut[self.node_index]
    self.compact(to_prune,lut)
    return self

def contractDR(self, to_keep):
    """
    Direct rule for contracting any max-tree nodes marked as False in 'to_keep'.
    This is a generic node removal procedure. Note that a node in the max-tree 
    can represent many level components.
    """
        
    to_keep[0] = True # The root can never be removed
    N = self.node_array.shape[1]
    lut = np.arange(N, dtype = np.int32)
    self.contract_dr_aux(to_keep.astype(np.int32),lut,self.node_array[0,:])
    self.node_index = lut[self.node_index]
    self.compact(~to_keep,lut)
    self.node_array[1,:] = 0
    self.update_nchild_aux(self.node_array[0,:],self.node_array[1,:])
    return self 

def getAncestors(self, node):
    return self.get_ancestors_aux(node, self.node_array[0,:])


def getChildren(self,node = 0):
    if not self._children_updated:
        self._cum_children_hist = self.node_array[1,:].cumsum().astype(np.int32)
        par = self.node_array[0,:]
        self._children_list = self.get_children_aux(self._cum_children_hist.copy(),par)
        self._children_updated = True
    if node == 0:
        return self._children_list[0:self._cum_children_hist[node]]
    else:
        return self._children_list[self._cum_children_hist[node-1]:self._cum_children_hist[node]]



def generateGraph(self, keep = [],nodes_attr = [], LR = False,file_name = "graph" ):
    n_nodes = self.node_array.shape[1]
    h = self.node_array[2,:]
    if keep == []:
        keep = np.ones(n_nodes, dtype = bool)
    if nodes_attr == []:
        nodes_attr = self.node_array[3,:]   # Default attribute is area

    G = gvgen.GvGen()
    G.styleAppend("remove", "style", "dashed")

    G.styleAppend("keep", "color","red")
    G.styleAppend("keep", "style","filled")
    items = {}


    for i in xrange(n_nodes):
        if keep[i]:
            items[i] = G.newItem('%d: %d [%d]' %(i,h[i],nodes_attr[i]))
            G.styleApply("keep", items[i])
        else:
            items[i] = G.newItem('%d: %d [%d]' %(i,h[i],nodes_attr[i]))
            G.styleApply("remove", items[i])
        pindex = self.node_array[0,i]
        if pindex != i:
            G.newLink(items[i], items[pindex])
    fd = StringIO.StringIO()
    G.dot(fd)
    dottext = fd.getvalue()

    if LR:
        dottext = dottext.replace("TB","RL")
        dottext = dottext.replace("{","{rankdir=LR")

    text_file = open(file_name + ".dot", "w")
    text_file.write(dottext)
    text_file.close()	
    try:
        os.system("/usr/bin/dot -Tpng %s.dot  > %s.png" %(file_name,file_name))
	os.remove(file_name + ".dot")
    except:
	print "Unable to save graph image. The method will return just the GraphViz code"
        os.remove(file_name + ".dot")
        return dottext
    return

def getDescendants(self, node):
    if self._children_updated == False:
        self.getChildren()
    if node == 0:
        return np.arange(self.node_array.shape[1], dtype = np.int32)
    elif self.node_array[1,node] == 0:
        return np.array([node],dtype = np.int32)
    else:
        return self.get_descendants_aux(node,self._children_list,self._cum_children_hist)


def getSubBranches(self,sb_index = 0):

    if self._sb_updated == False:
        visited = np.zeros(self.node_array.shape[1], dtype = np.int32)
        self._sb = np.zeros_like(visited)
        self._cum_sb_hist = self.get_sub_branches_aux(self.node_array[0,:],\
                                                      self.node_array[1,:],\
                                                      self._sb, visited)
        self._cum_sb_hist = np.concatenate((np.array([0],dtype = np.int32),\
                                           self._cum_sb_hist),axis = 0)
        self._sb_updated = True
    return self._sb[self._cum_sb_hist[sb_index]:self._cum_sb_hist[sb_index+1]]




def generateCCGraph(self,s = (100,100), parent_scale = True, LR = False,file_name = "graph"):
    n_nodes = self.node_array.shape[1]
    G = gvgen.GvGen()
    parents = self.node_array[0,:]
    G.styleAppend("node", "fontcolor", "transparent")
    G.styleAppend("node", "shape", "rectangle")
    items = {}
    items[0] = G.newItem(str(0))
    G.styleApply("node", items[0])
    for i in xrange(1,n_nodes):
        items[i] = G.newItem("")
        path = 'node___' + str(i) + '.png'

        if parent_scale:
            xpmin,xpmax = self.node_array[6,parents[i]],self.node_array[7,parents[i]]
            ypmin,ypmax = self.node_array[9,parents[i]],self.node_array[10,parents[i]]
        else:
            xpmin,xpmax = self.node_array[6,i],self.node_array[7,i]
            ypmin,ypmax = self.node_array[9,i],self.node_array[10,i]
	node_image = cv2.resize(node_image,(s[1],s[0]))

        if parent_scale:
            bool_image = np.zeros(s,dtype = bool)
            indexes = np.nonzero(node_image)
            if indexes[0].size:
                ymin,ymax = indexes[0].min(),indexes[0].max()
                xmin,xmax = indexes[1].min(),indexes[1].max()
                bool_image[ymin:ymax+1,xmin] = 1
                bool_image[ymin:ymax+1,xmax] = 1
                bool_image[ymin,xmin:xmax+1] = 1
                bool_image[ymax,xmin:xmax+1] = 1
                #node_image = ia870.iagshow(node_image,bool_image)
                node_image = np.array([node_image,node_image,node_image])
                node_image[0][bool_image] = 255
                node_image[1][bool_image] = 0
                node_image[2][bool_image] = 0

        if node_image.ndim == 3:
            cv2.imwrite(path, node_image.transpose(1,2,0))
        else:
            cv2.imwrite(path, cv2.cvtColor(node_image,cv2.COLOR_GRAY2RGB))
        
        G.propertyAppend(items[i],"image", path)
        G.styleApply("node", items[i])
        pindex = parents[i]
        if pindex != i:
            G.newLink(items[i], items[pindex])

    fd = StringIO.StringIO()
    G.dot(fd)
    dottext = fd.getvalue()
    if LR:
        dottext = dottext.replace("TB","RL")
        dottext = dottext.replace("{","{rankdir=LR")

    text_file = open(file_name + ".dot", "w")
    text_file.write(dottext)
    text_file.close()	
    try:
        os.system("/usr/bin/dot -Tpng %s.dot  > %s.png" %(file_name,file_name))
        os.remove(file_name + ".dot")
        files = os.listdir('.')
        for f in files:
            if f.startswith("node___"):
                os.remove(f)
    except:
        print "Unable to save graph image. The method will return just the GraphViz code. Lots of temporary files were generated in your current folder."
        os.remove(file_name + ".dot")
        return dottext
    return


def generateCCPathGraph(self,start, end = 0, s = (100,100), parent_scale = True, \
                        composite_nodes = True, LR = False,file_name = "graph"):
    G = gvgen.GvGen()
    parents = self.node_array[0,:]
    h = self.node_array[2,:]
    nlevels = h - h[parents]
    G.styleAppend("node", "fontcolor", "transparent")
    G.styleAppend("node", "shape", "rectangle")
    items = {}
    pos = start
    items[pos] = G.newItem("")
    j = 1000000
    while True:
        path = 'node___' + str(pos) + '.png'

        if parent_scale and pos!= end:
            xpmin,xpmax = self.node_array[6,parents[pos]],self.node_array[7,parents[pos]]
            ypmin,ypmax = self.node_array[9,parents[pos]],self.node_array[10,parents[pos]]
        else:
            xpmin,xpmax = self.node_array[6,pos],self.node_array[7,pos]
            ypmin,ypmax = self.node_array[9,pos],self.node_array[10,pos]

        node_image = (self.recConnectedComponent(pos)[xpmin:xpmax+1,ypmin:ypmax+1]).astype('uint8')*255
        node_image = cv2.resize(node_image,(s[1],s[0]))

        if parent_scale and pos!= end:
            bool_image = np.zeros(s,dtype = bool)
            indexes = np.nonzero(node_image)
            if indexes[0].size:
                ymin,ymax = indexes[0].min(),indexes[0].max()
                xmin,xmax = indexes[1].min(),indexes[1].max()
                bool_image[ymin:ymax+1,xmin] = 1
                bool_image[ymin:ymax+1,xmax] = 1
                bool_image[ymin,xmin:xmax+1] = 1
                bool_image[ymax,xmin:xmax+1] = 1
                #node_image = ia870.iagshow(node_image,bool_image)
                node_image = np.array([node_image,node_image,node_image])
                node_image[0][bool_image] = 255
                node_image[1][bool_image] = 0
                node_image[2][bool_image] = 0
	
        if node_image.ndim == 3:
            cv2.imwrite(path, node_image.transpose(1,2,0))
        else:
            cv2.imwrite(path, cv2.cvtColor(node_image,cv2.COLOR_GRAY2RGB))
        #items[pos] = G.newItem("")
        G.propertyAppend(items[pos],"image", path)
        G.styleApply("node", items[pos])

        if nlevels[pos] > 1 and composite_nodes:
            items[j] = G.newItem("")
            G.propertyAppend(items[j],"image", path)
            G.styleApply("node", items[j])
            G.newLink(items[pos], items[j])
            j += 1
            for i in xrange(nlevels[pos] - 2):
                items[j] = G.newItem("")
                G.propertyAppend(items[j],"image", path)
                G.styleApply("node", items[j])
                G.newLink(items[j - 1], items[j])
                j +=1


        if pos == end:
            break
        pindex = parents[pos]
        items[pindex] = G.newItem("")
        if nlevels[pos] > 1 and composite_nodes:
            G.newLink(items[j-1], items[pindex])
        else:
            G.newLink(items[pos], items[pindex])
        pos = pindex

    fd = StringIO.StringIO()
    G.dot(fd)
    dottext = fd.getvalue()
    dottext = dottext.replace("TB","RL")
    dottext = dottext.replace("{","{rankdir=LR")
   
    text_file = open(file_name + ".dot", "w")
    text_file.write(dottext)
    text_file.close()	
    try:
        os.system("/usr/bin/dot -Tpng %s.dot  > %s.png" %(file_name,file_name))
        os.remove(file_name + ".dot")
        files = os.listdir('.')
        for f in files:
            if f.startswith("node___"):
                os.remove(f)
    except:
        print "Unable to save graph image. The method will return just the GraphViz code. Lots of temporary files were generated in your current folder."
        os.remove(file_name + ".dot")
        return dottext
    return

def recConnectedComponent(self,node, bbonly = False):
    """
    This method returns a binary image corresponding to the
    connected component represented by node.
    bbonly -> Flag that indicates wether return the whole 
    image or just the connecetd component bounding-box.
    """
    seed = self.node_array[4,node]
    cc = np.zeros(self.node_index.shape, dtype = np.uint8)
        
    if self.node_index.ndim == 2:
       self.rec_connected_component_2d_aux(int(node),int(seed),self.node_index,cc,self.off)
    else:
       self.rec_connected_component_3d_aux(int(node),int(seed),self.node_index,cc,self.off)
        
    if not bbonly:
       return cc.astype(bool)

    xmin,xmax = self.node_array[6,node], self.node_array[7,node] + 1
    ymin,ymax = self.node_array[9,node], self.node_array[10,node] + 1
    if self.node_index.ndim == 2:
       indexes = (slice(xmin,xmax),slice(ymin,ymax))
    else:
       zmin,zmax = self.node_array[12,node], self.node_array[13,node] + 1
       indexes = (slice(xmin,xmax),slice(ymin,ymax),slice(zmin,zmax))
    return cc[indexes].astype(bool)




def computeHistogram(self,img,nbins = 256,wimg = [], normalize = True):
    """
    This method computes histograms of the max-tree nodes.
    Input:
       - img, 2d-array int32. Image used to compute the histograms.
       - wimg, 2d-array int32. Weight image used in the histogram computation.
       - nbins, int. Number of histogram bins. It starts in 0 and ends in nbins - 1.
       - normalize, bool. Flag indicating whether the histogram should be normalized or not. 
    Output
       - img, 2d-array float. Histogram array. Each line corresponds to a node histogram.
    """
    hist = np.zeros((self.node_array.shape[1],nbins), dtype = np.int32)    
    if wimg == []:
        hist[self.node_index,img] += 1
    else:
        hist[self.node_index,img] += wimg
        self.compute_hist_aux(self.node_array[0],hist)
    if normalize:
        hist = hist*1.0/hist.sum(axis = 1).reshape(-1,1) 
    return hist.astype(float)

def getBifAncestor(self, node):
    return self.get_bif_ancestor_aux(node, self.node_array[0,:],self.node_array[1,:])

def computeNodeGrayAvg(self):
    """
    This method computes the gray-level average of
    the max-tree nodes.
    """
    gray_avg = np.zeros(self.node_array.shape[1], dtype = np.float)
    self.compute_node_gray_avg_aux(self.node_array[0,:],self.node_array[2,:],self.node_array[3,:].copy(),gray_avg)
    gray_avg = (gray_avg)/self.node_array[3,:]
    return gray_avg


def computeNodeGrayVar(self,gray_avg = [] ):
    """
    This method computes the gray-level standard deviation of
    the max-tree nodes.
    """
    if gray_avg == []:
        gray_avg = self.computeNodeGrayAvg()
                
    gray_var = np.zeros(self.node_array.shape[1], dtype = np.float)
    squared_gray_avg = np.zeros(self.node_array.shape[1], dtype = np.float)
    self.compute_node_gray_var_aux(self.node_array[0,:],self.node_array[2,:],self.node_array[3,:].copy(),squared_gray_avg)
    squared_gray_avg = squared_gray_avg/self.node_array[3,:]
    gray_var = (squared_gray_avg - gray_avg**2)
    return gray_var


def computeEccentricity(self):
    """
    This method computes the eccentricity
    of the max-tree nodes.
    """
            
    xx = np.zeros((self.node_array.shape[1]),dtype = np.int32)
    yy = np.zeros((self.node_array.shape[1]),dtype = np.int32)
    xy = np.zeros((self.node_array.shape[1]),dtype = np.int32)
    par = self.node_array[0,:]
    self.compute_eccentricity_aux(xx,yy,xy,par,self.node_index)
    area = self.node_array[3,:]
    xc = 1.0*self.node_array[5,:]/area
    yc = 1.0*self.node_array[8,:]/area
    m20 = 1.0*xx /area - xc**2
    m02 = 1.0*yy/area - yc**2
    m11 = 1.0*xy/area - xc*yc
    aux1 = (m20 + m02)/2
    aux2 = 4*m11**2 + (m20-m02)**2
    aux2 = np.sqrt(aux2)/2
    L1 = aux1 + aux2
    L2 = aux1 - aux2
    ecc = np.sqrt(1 - L2/L1)
    ecc[np.isnan(ecc)] = 1
    return ecc,L1,L2

