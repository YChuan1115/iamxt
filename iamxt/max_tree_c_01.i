%module max_tree_c_01
%{
#define SWIG_FILE_WITH_INIT
#undef NO_IMPORT_ARRAY
%}

%include "typemaps.i"
%include "numpy.i"

%init %{
import_array();
%}

%{

void counting_sort_c(int , unsigned char *, int **, int *);

void canonicalize_c(int , unsigned char *, int , int *,
                    int , int *);

void union_find2d_c(int H,int W, int ,int , int *,int , int *,
                    int , int *,int , int *, int ,
                    unsigned char *);

void computeNodeArray2d_c(int , int *,int , unsigned char *, int ,
                          int * ,int , int , int *,
                          int **, int *, int *);

void union_find3d_c(int L,int M, int N, int ,int , int *,int ,
                    int *, int , int *,int ,
                    int *, int , unsigned char *);

void computeNodeArray3d_c(int , int *,int , unsigned char *,
                          int , int * ,int , int , int , int *,
                          int **, int *, int *);


void compute_area_c(int , int *, int , int *, int , int *);

void direct_filter_c(double lambda, int , int *, int , int *,
 int , unsigned char *, int , unsigned char *, int , double * );

%}

%feature("autodoc", 1);
void counting_sort_c(int DIM1, unsigned char *IN_ARRAY1, int **ARGOUT_ARRAY1, int *DIM1);

void canonicalize_c(int DIM1, unsigned char *INPLACE_ARRAY1, int DIM1, int *INPLACE_ARRAY1,
                    int DIM1, int *INPLACE_ARRAY1);

void union_find2d_c(int H,int W, int DIM1,int DIM2, int *INPLACE_ARRAY2,int DIM1, int *INPLACE_ARRAY1,
                    int DIM1, int *INPLACE_ARRAY1,int DIM1, int *INPLACE_ARRAY1, int DIM1,
                    unsigned char *INPLACE_ARRAY1);

void computeNodeArray2d_c(int DIM1, int *IN_ARRAY1,int DIM1, unsigned char *IN_ARRAY1, int DIM1,
                          int *IN_ARRAY1 ,int DIM1, int DIM2, int *INPLACE_ARRAY2,
                          int **ARGOUT_ARRAY2, int *DIM1, int *DIM2);

void union_find3d_c(int L,int M, int N, int DIM1,int DIM2, int *INPLACE_ARRAY2,int DIM1,
                    int *INPLACE_ARRAY1, int DIM1, int *INPLACE_ARRAY1,int DIM1,
                    int *INPLACE_ARRAY1, int DIM1, unsigned char *INPLACE_ARRAY1);

void computeNodeArray3d_c(int DIM1, int *INPLACE_ARRAY1,int DIM1, unsigned char *INPLACE_ARRAY1,
                          int DIM1, int *INPLACE_ARRAY1 ,int DIM1, int DIM2, int DIM3, int 
                          *INPLACE_ARRAY3, int **ARGOUT_ARRAY2, int *DIM1, int *DIM2);

void compute_area_c(int DIM1, int *INPLACE_ARRAY1, int DIM1, int *INPLACE_ARRAY1, int DIM1, int *INPLACE_ARRAY1);

void direct_filter_c(double lambda, int DIM1, int *INPLACE_ARRAY1, int DIM1, int *INPLACE_ARRAY1,
 int DIM1, unsigned char *INPLACE_ARRAY1, int DIM1, unsigned char *INPLACE_ARRAY1, int DIM1, double *INPLACE_ARRAY1 );

